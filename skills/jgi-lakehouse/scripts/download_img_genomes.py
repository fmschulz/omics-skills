#!/usr/bin/env python3
"""
Download microbial genomes with IMG taxon OIDs from JGI Lakehouse + Filesystem.

Usage:
    python download_img_genomes.py [--count N] [--domain DOMAIN] [--output-dir DIR]

Examples:
    python download_img_genomes.py --count 5 --domain Bacteria
    python download_img_genomes.py --count 3 --domain Archaea --output-dir my_genomes
"""

import argparse
import json
import os
import shutil
import tarfile
import time
from pathlib import Path

import requests

# Configuration
DREMIO_HOST = os.getenv("DREMIO_HOST", "lakehouse-1.jgi.lbl.gov")
DREMIO_PORT = os.getenv("DREMIO_PORT", "9047")
DREMIO_BASE_URL = f"https://{DREMIO_HOST}:{DREMIO_PORT}/api/v3"
DREMIO_REQUEST_TIMEOUT = float(os.getenv("DREMIO_REQUEST_TIMEOUT", "60"))
TLS_DISABLED_VALUES = {"0", "false", "no", "off"}
ALLOWED_DOMAINS = {"Archaea", "Bacteria", "Eukaryota", "Viruses"}
MAX_QUERY_LIMIT = 5000

# JGI Filesystem paths
IMG_DOWNLOAD_DIR = Path(
    os.getenv("IMG_DOWNLOAD_DIR", "/clusterfs/jgi/img_merfs-ro/img_web/img_web_data/download")
)
IMG_DATA_DIR = Path(os.getenv("IMG_DATA_DIR", "/clusterfs/jgi/img_merfs-ro/img_web_data_merfs"))


def verify_tls() -> bool:
    """Return whether Dremio HTTPS requests should verify TLS certificates."""
    return os.getenv("DREMIO_VERIFY_TLS", "1").strip().lower() not in TLS_DISABLED_VALUES


def validate_domain(domain: str) -> str:
    """Whitelist IMG domain values before building SQL text."""
    if domain not in ALLOWED_DOMAINS:
        allowed = ", ".join(sorted(ALLOWED_DOMAINS))
        raise ValueError(f"Unsupported domain {domain!r}. Allowed values: {allowed}")
    return domain


def validate_limit(limit: int) -> int:
    limit = int(limit)
    if limit < 1 or limit > MAX_QUERY_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_QUERY_LIMIT}")
    return limit


def bounded_count_arg(value: str) -> int:
    """argparse type for --count with a clean CLI error instead of a traceback."""
    try:
        return validate_limit(int(value))
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def safe_extract_tar(tar: tarfile.TarFile, extract_dir: Path) -> None:
    """Extract a tarball after rejecting members that escape extract_dir."""
    base = extract_dir.resolve()
    for member in tar.getmembers():
        target = (base / member.name).resolve()
        if not _is_relative_to(target, base):
            raise ValueError(f"Unsafe tar member path: {member.name}")
        if member.issym() or member.islnk():
            link_target = (target.parent / member.linkname).resolve()
            if not _is_relative_to(link_target, base):
                raise ValueError(f"Unsafe tar link target: {member.name} -> {member.linkname}")
    try:
        tar.extractall(base, filter="data")
    except TypeError:
        tar.extractall(base)


def get_token():
    """Get Dremio token from environment or file."""
    token = os.getenv("DREMIO_PAT")
    if not token:
        token_path = Path.home() / ".secrets" / "dremio_pat"
        if token_path.exists():
            token = token_path.read_text().strip()
    if not token:
        raise ValueError("DREMIO_PAT not set. Run: export DREMIO_PAT=$(cat ~/.secrets/dremio_pat)")
    return token


def query(sql: str, limit: int = 100) -> list:
    """Execute SQL query against Lakehouse."""
    limit = validate_limit(limit)
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Submit query
    response = requests.post(
        f"{DREMIO_BASE_URL}/sql",
        headers=headers,
        json={"sql": sql},
        timeout=DREMIO_REQUEST_TIMEOUT,
        verify=verify_tls(),
    )
    response.raise_for_status()
    job_id = response.json().get("id")

    # Wait for completion
    while True:
        status = requests.get(
            f"{DREMIO_BASE_URL}/job/{job_id}",
            headers=headers,
            timeout=DREMIO_REQUEST_TIMEOUT,
            verify=verify_tls(),
        )
        status.raise_for_status()
        status_json = status.json()

        if status_json.get("jobState") == "COMPLETED":
            break
        elif status_json.get("jobState") in ("FAILED", "CANCELED", "CANCELLED"):
            raise RuntimeError(f"Query failed: {status_json.get('errorMessage')}")
        time.sleep(1)

    # Get results
    results = requests.get(
        f"{DREMIO_BASE_URL}/job/{job_id}/results",
        headers=headers,
        params={"limit": limit},
        timeout=DREMIO_REQUEST_TIMEOUT,
        verify=verify_tls(),
    )
    results.raise_for_status()
    return results.json().get("rows", [])


def find_genomes(domain: str = "Bacteria", limit: int = 100) -> list:
    """Query Lakehouse for finished isolate genomes."""
    domain = validate_domain(domain)
    limit = validate_limit(limit)
    sql = f"""
    SELECT
        taxon_oid,
        taxon_display_name,
        domain,
        phylum,
        genus,
        species,
        seq_status,
        genome_type,
        sequencing_gold_id
    FROM "img-db-2 postgresql".img_core_v400.taxon
    WHERE domain = '{domain}'
      AND genome_type = 'isolate'
      AND is_public = 'Yes'
      AND seq_status = 'Finished'
    ORDER BY taxon_oid DESC
    LIMIT {limit}
    """
    return query(sql, limit=limit)


def check_file_availability(taxon_oid: str) -> dict:
    """Check if genome files exist on filesystem."""
    tar_path = IMG_DOWNLOAD_DIR / f"{taxon_oid}.tar.gz"
    data_path = IMG_DATA_DIR / taxon_oid

    result = {"taxon_oid": taxon_oid, "available": False}

    if tar_path.exists():
        result["available"] = True
        result["type"] = "tar.gz"
        result["path"] = str(tar_path)
        result["size_mb"] = tar_path.stat().st_size / (1024 * 1024)
    elif data_path.exists():
        result["available"] = True
        result["type"] = "directory"
        result["path"] = str(data_path)

    return result


def download_genome(taxon_oid: str, output_dir: Path) -> dict:
    """Download and extract genome package."""
    availability = check_file_availability(taxon_oid)

    if not availability["available"]:
        return {"success": False, "error": "Files not found on filesystem"}

    output_dir.mkdir(parents=True, exist_ok=True)

    if availability["type"] == "tar.gz":
        src = Path(availability["path"])
        dst = output_dir / src.name

        # Copy tar.gz
        shutil.copy2(src, dst)

        # Extract
        extract_dir = output_dir / taxon_oid
        extract_dir.mkdir(exist_ok=True)

        with tarfile.open(dst, "r:gz") as tar:
            safe_extract_tar(tar, extract_dir)

        return {
            "success": True,
            "taxon_oid": taxon_oid,
            "tar_file": str(dst),
            "extracted_dir": str(extract_dir),
            "size_mb": availability["size_mb"]
        }

    elif availability["type"] == "directory":
        # Copy key files from data directory
        src_dir = Path(availability["path"])
        dst_dir = output_dir / taxon_oid
        dst_dir.mkdir(exist_ok=True)

        # Copy available files
        files_copied = []
        for pattern in ["assembled/rRNA_16S.fna", "assembled/taxon_stats.txt"]:
            src_file = src_dir / pattern
            if src_file.exists():
                dst_file = dst_dir / src_file.name
                shutil.copy2(src_file, dst_file)
                files_copied.append(src_file.name)

        return {
            "success": True,
            "taxon_oid": taxon_oid,
            "directory": str(dst_dir),
            "files_copied": files_copied
        }

    return {"success": False, "error": "Unknown file type"}


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Download IMG genomes from JGI Lakehouse")
    parser.add_argument("--count", type=bounded_count_arg, default=5, help="Number of genomes to download")
    parser.add_argument("--domain", default="Bacteria", choices=sorted(ALLOWED_DOMAINS), help="IMG domain")
    parser.add_argument("--output-dir", default="img_genomes", help="Output directory")
    args = parser.parse_args(argv)
    count = args.count

    output_dir = Path(args.output_dir)

    print("=" * 70)
    print(f"Downloading {count} {args.domain} genomes from JGI Lakehouse")
    print("=" * 70)

    # Step 1: Query Lakehouse
    print(f"\n1. Querying Lakehouse for {args.domain} isolate genomes...")
    genomes = find_genomes(domain=args.domain, limit=100)
    print(f"   Found {len(genomes)} genomes in Lakehouse")

    # Step 2: Check file availability
    print("\n2. Checking filesystem availability...")
    available = []
    for g in genomes:
        taxon_oid = str(g.get("taxon_oid"))
        avail = check_file_availability(taxon_oid)
        if avail["available"]:
            g.update(avail)
            available.append(g)
            if len(available) >= count * 2:  # Get more than needed for diversity
                break

    print(f"   Found {len(available)} genomes with files available")

    # Step 3: Select diverse genomes
    print(f"\n3. Selecting {count} diverse genomes...")
    selected = []
    phyla_seen = set()

    for g in available:
        phylum = g.get("phylum", "Unknown")
        if phylum not in phyla_seen and len(selected) < count:
            selected.append(g)
            phyla_seen.add(phylum)

    # Fill remaining
    for g in available:
        if g not in selected and len(selected) < count:
            selected.append(g)

    # Step 4: Download
    print(f"\n4. Downloading {len(selected)} genomes to {output_dir}/...")
    print("-" * 70)

    results = []
    for g in selected:
        taxon_oid = str(g.get("taxon_oid"))
        name = g.get("taxon_display_name", "Unknown")
        print(f"\n   {name}")
        print(f"   Taxon OID: {taxon_oid}")

        result = download_genome(taxon_oid, output_dir)
        result["name"] = name
        result["phylum"] = g.get("phylum")
        results.append(result)

        if result["success"]:
            print(f"   ✓ Downloaded successfully")
        else:
            print(f"   ✗ Failed: {result.get('error')}")

    # Save metadata
    metadata_file = output_dir / "downloaded_genomes.json"
    with open(metadata_file, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    successful = [r for r in results if r.get("success")]
    print(f"\nDownloaded {len(successful)} genomes to {output_dir}/")
    for r in successful:
        print(f"  - {r.get('taxon_oid')}: {r.get('name')}")
    print(f"\nMetadata saved to: {metadata_file}")


if __name__ == "__main__":
    main()
