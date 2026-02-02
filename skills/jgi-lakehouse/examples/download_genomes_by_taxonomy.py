#!/usr/bin/env python3
"""
Example: Download genomes from NCBI based on JGI Lakehouse taxonomy queries

This example demonstrates how to:
1. Query the Lakehouse for genomes by taxonomic family/genus
2. Extract NCBI assembly accessions from GOLD metadata
3. Download genomes efficiently using NCBI datasets CLI

IMPORTANT NOTES:
- The Lakehouse contains genome METADATA but NOT actual sequences
- Use NCBI accessions from Lakehouse to download from GenBank
- The `ncbi_assembly` table links GOLD projects to NCBI assemblies
- Always filter for public data with `is_public = 'Yes'`

Prerequisites:
    # Install NCBI datasets CLI (via pixi/conda)
    pixi add ncbi-datasets-cli

    # Set Dremio token
    export DREMIO_PAT=$(cat ~/.secrets/dremio_pat)

Usage:
    python download_genomes_by_taxonomy.py <family_name> [output_dir]

Examples:
    python download_genomes_by_taxonomy.py Midichloriaceae
    python download_genomes_by_taxonomy.py Rickettsiaceae ./rickettsia_genomes
    python download_genomes_by_taxonomy.py Rhodobacteraceae ./rhodobacter_genomes
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Add parent scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from rest_client import query


def find_genomes_by_family(family_pattern: str, limit: int = 100) -> list[dict]:
    """
    Find genomes by taxonomic family with NCBI assembly accessions.

    Args:
        family_pattern: Family name pattern (e.g., 'Midichloriaceae', 'Rickettsia')
        limit: Maximum results to return

    Returns:
        List of genome records with NCBI accessions
    """
    sql = f'''
    SELECT DISTINCT
        p.gold_id,
        p.project_name,
        p.ncbi_taxonomy_name,
        p.seq_status,
        o.organism_name,
        o.genus,
        o.family AS organism_family,
        o.ncbi_taxon_id,
        a.ncbi_assembly_accession,
        a.assembly_name,
        a.assembly_level,
        a.genome_size,
        a.gc_percent,
        a.contig_count
    FROM "gold-db-2 postgresql".gold.project p
    LEFT JOIN "gold-db-2 postgresql".gold.organism_v2 o
        ON p.organism_id = o.organism_id
    LEFT JOIN "gold-db-2 postgresql".gold.ncbi_assembly a
        ON p.project_id = a.project_id
    WHERE (
        p.ncbi_taxonomy_name LIKE '%{family_pattern}%'
        OR o.family LIKE '%{family_pattern}%'
        OR o.organism_name LIKE '%{family_pattern}%'
    )
    AND p.is_public = 'Yes'
    AND a.ncbi_assembly_accession IS NOT NULL
    ORDER BY a.assembly_level, a.genome_size DESC
    LIMIT {limit}
    '''

    return query(sql, timeout=300, limit=limit)


def get_ecosystem_info(gold_ids: list[str]) -> dict[str, dict]:
    """
    Get ecosystem/environmental info for GOLD projects.

    Args:
        gold_ids: List of GOLD project IDs

    Returns:
        Dict mapping gold_id to ecosystem info
    """
    if not gold_ids:
        return {}

    gold_list = "', '".join(gold_ids)
    sql = f'''
    SELECT
        p.gold_id,
        s.ecosystem,
        s.ecosystem_category,
        s.ecosystem_type,
        s.ecosystem_subtype,
        s.specific_ecosystem
    FROM "gold-db-2 postgresql".gold.project p
    JOIN "gold-db-2 postgresql".gold.study s ON p.master_study_id = s.study_id
    WHERE p.gold_id IN ('{gold_list}')
    '''

    results = query(sql, timeout=120)
    return {r['gold_id']: r for r in results}


def download_genomes(accessions: list[str], output_dir: Path, include_gff: bool = True) -> bool:
    """
    Download genomes from NCBI using datasets CLI.

    Args:
        accessions: List of NCBI assembly accessions (GCA_*)
        output_dir: Directory to save downloaded files
        include_gff: Include GFF annotations

    Returns:
        True if successful
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_file = output_dir / "genomes.zip"

    # Build datasets command
    includes = ["genome", "protein"]
    if include_gff:
        includes.append("gff3")

    cmd = [
        "datasets", "download", "genome", "accession",
        *accessions,
        "--include", ",".join(includes),
        "--filename", str(zip_file)
    ]

    print(f"Downloading {len(accessions)} genomes...")
    print(f"Command: {' '.join(cmd[:6])} [accessions...] --include {','.join(includes)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Downloaded to: {zip_file}")

        # Extract
        subprocess.run(["unzip", "-o", str(zip_file), "-d", str(output_dir)],
                      capture_output=True, check=True)
        print(f"Extracted to: {output_dir}")

        return True
    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("ERROR: 'datasets' CLI not found. Install with: pixi add ncbi-datasets-cli")
        return False


def summarize_genomes(genomes: list[dict]) -> dict:
    """Summarize genome statistics."""
    if not genomes:
        return {}

    sizes = [g['genome_size'] for g in genomes if g.get('genome_size')]
    gc = [g['gc_percent'] for g in genomes if g.get('gc_percent')]

    by_level = {}
    for g in genomes:
        level = g.get('assembly_level', 'Unknown')
        by_level[level] = by_level.get(level, 0) + 1

    return {
        'total': len(genomes),
        'by_assembly_level': by_level,
        'size_range_mb': (min(sizes)/1e6, max(sizes)/1e6) if sizes else (0, 0),
        'gc_range': (min(gc), max(gc)) if gc else (0, 0),
        'genera': list(set(g.get('genus') for g in genomes if g.get('genus')))
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python download_genomes_by_taxonomy.py <family_pattern> [output_dir]")
        print("\nExamples:")
        print("  python download_genomes_by_taxonomy.py Midichloriaceae")
        print("  python download_genomes_by_taxonomy.py Rickettsiaceae ./rickettsia")
        sys.exit(1)

    family_pattern = sys.argv[1]
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"./{family_pattern.lower()}_genomes")

    print(f"Searching Lakehouse for: {family_pattern}")
    print("=" * 60)

    # Step 1: Query Lakehouse for genomes
    genomes = find_genomes_by_family(family_pattern)

    if not genomes:
        print(f"No genomes found matching '{family_pattern}'")
        sys.exit(0)

    # Step 2: Summarize findings
    summary = summarize_genomes(genomes)
    print(f"\nFound {summary['total']} genomes")
    print(f"Assembly levels: {summary['by_assembly_level']}")
    print(f"Size range: {summary['size_range_mb'][0]:.2f} - {summary['size_range_mb'][1]:.2f} Mb")
    print(f"GC range: {summary['gc_range'][0]:.1f}% - {summary['gc_range'][1]:.1f}%")
    print(f"Genera: {', '.join(summary['genera'][:5])}{'...' if len(summary['genera']) > 5 else ''}")

    # Step 3: Get ecosystem info
    gold_ids = [g['gold_id'] for g in genomes if g.get('gold_id')]
    ecosystem_info = get_ecosystem_info(gold_ids)

    ecosystems = set()
    for eco in ecosystem_info.values():
        if eco.get('ecosystem'):
            ecosystems.add(eco['ecosystem'])
    if ecosystems:
        print(f"Ecosystems: {', '.join(ecosystems)}")

    # Step 4: Show genomes to download
    print("\n" + "=" * 60)
    print("GENOMES AVAILABLE FOR DOWNLOAD")
    print("=" * 60)

    # Prefer complete genomes, then scaffolds, then contigs
    level_order = {'Complete Genome': 0, 'Chromosome': 1, 'Scaffold': 2, 'Contig': 3}
    sorted_genomes = sorted(genomes, key=lambda g: level_order.get(g.get('assembly_level', ''), 4))

    for g in sorted_genomes[:10]:
        size_mb = g['genome_size'] / 1e6 if g.get('genome_size') else 0
        print(f"\n  {g['ncbi_assembly_accession']} | {g.get('assembly_level', 'N/A')}")
        print(f"    {g.get('organism_name', g.get('project_name', 'Unknown'))[:50]}")
        print(f"    Size: {size_mb:.2f} Mb | GC: {g.get('gc_percent', 'N/A')}%")

    if len(sorted_genomes) > 10:
        print(f"\n  ... and {len(sorted_genomes) - 10} more")

    # Step 5: Save metadata
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_file = output_dir / "lakehouse_metadata.json"

    metadata = {
        'query': family_pattern,
        'summary': summary,
        'ecosystems': list(ecosystems),
        'genomes': genomes
    }

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"\nMetadata saved to: {metadata_file}")

    # Step 6: Offer download
    accessions = [g['ncbi_assembly_accession'] for g in genomes if g.get('ncbi_assembly_accession')]

    print("\n" + "=" * 60)
    print("TO DOWNLOAD THESE GENOMES")
    print("=" * 60)
    print(f"""
# Option 1: Download all {len(accessions)} genomes
pixi run datasets download genome accession {' '.join(accessions[:3])} ... \\
    --include genome,gff3,protein --filename {output_dir}/genomes.zip

# Option 2: Download only complete genomes
complete = [a for a in sorted_genomes if a.get('assembly_level') == 'Complete Genome']
# Found {len([g for g in genomes if g.get('assembly_level') == 'Complete Genome'])} complete genomes

# Option 3: Use this script's download function (uncomment below)
""")

    # Uncomment to auto-download:
    # download_genomes(accessions, output_dir)

    print(f"Accessions file: {output_dir}/accessions.txt")
    with open(output_dir / "accessions.txt", 'w') as f:
        f.write('\n'.join(accessions))


if __name__ == "__main__":
    if not os.environ.get("DREMIO_PAT"):
        print("ERROR: DREMIO_PAT environment variable not set")
        print("Run: export DREMIO_PAT=$(cat ~/.secrets/dremio_pat)")
        sys.exit(1)

    main()
