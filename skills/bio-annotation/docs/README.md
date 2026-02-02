# Bio-Annotation Tool Documentation

This directory contains practical usage guides for the core bioinformatics tools used in the bio-annotation skill workflow.

## Documentation Overview

Each tool has a dedicated markdown file with comprehensive usage information including installation, command-line options, common examples, and performance tips.

## Available Tool Guides

### [DIAMOND](diamond-usage.md)
**Version**: v2.1.6+
**Purpose**: Accelerated BLAST-compatible sequence aligner
**Key Features**: 100x-10,000x faster than BLAST, protein and translated DNA searches
**Documentation**: [diamond-usage.md](diamond-usage.md)
**Official Site**: http://www.diamondsearch.org

### [TaxonKit](taxonkit-usage.md)
**Version**: v0.14.2-v0.20.0
**Purpose**: NCBI Taxonomy data manipulation toolkit
**Key Features**: Taxonomy resolution, lineage queries, TaxID conversion
**Documentation**: [taxonkit-usage.md](taxonkit-usage.md)
**Official Site**: https://bioinf.shenwei.me/taxonkit/

### [InterProScan](interproscan-usage.md)
**Version**: v5-6
**Purpose**: Protein function classification and domain prediction
**Key Features**: Integrates multiple signature databases, GO terms, pathway annotations
**Documentation**: [interproscan-usage.md](interproscan-usage.md)
**Official Site**: https://www.ebi.ac.uk/interpro/

### [eggNOG-mapper](eggnog-mapper-usage.md)
**Version**: v2.1.13
**Purpose**: Functional annotation through orthology assignment
**Key Features**: Fast genome-wide annotation, COG categories, KEGG pathways
**Documentation**: [eggnog-mapper-usage.md](eggnog-mapper-usage.md)
**Official Site**: http://eggnog-mapper.embl.de/

## Workflow Integration

These tools are used together in the bio-annotation workflow:

1. **InterProScan**: Domain and family annotation from protein signatures
2. **eggNOG-mapper**: Orthology-based functional annotation with GO, COG, and KEGG
3. **DIAMOND**: Fast sequence similarity search for taxonomy assignment
4. **TaxonKit**: Resolve taxonomy from DIAMOND TaxIDs to full lineages

## Quick Start Examples

### DIAMOND + TaxonKit Pipeline
```bash
# Sequence alignment with taxonomy
diamond blastp --query proteins.faa --db nr.dmnd \
  --out results.tsv --outfmt 6 qseqid sseqid staxids evalue bitscore \
  --threads 32 --sensitive

# Resolve taxonomy
cut -f3 results.tsv | taxonkit lineage -n -r | \
  taxonkit reformat -f "{k};{p};{c};{o};{f};{g};{s}" | \
  paste results.tsv - > results_with_taxonomy.tsv
```

### InterProScan Annotation
```bash
# Comprehensive protein annotation
interproscan.sh -i proteins.faa -o interpro_results \
  -f TSV,GFF3 -goterms -iprlookup -pathways -cpu 32
```

### eggNOG-mapper Annotation
```bash
# Orthology-based annotation
emapper.py -i proteins.faa -o eggnog_annotation \
  --data_dir $EGGNOG_DATA_DIR \
  --sensmode very-sensitive \
  --cpu 32 --report_orthologs
```

## Performance Optimization

### Resource Requirements

| Tool | CPU | Memory | Disk Space | Speed |
|------|-----|--------|------------|-------|
| DIAMOND | High | Moderate (8-32GB) | Low | Very Fast |
| TaxonKit | Low | Low (1-2GB) | Low | Very Fast |
| InterProScan | High | High (16-64GB) | Moderate | Slow |
| eggNOG-mapper | High | Moderate (8-32GB) | High (databases) | Fast |

### Optimization Tips

1. **DIAMOND**: Use `--sensitive` mode by default, increase to `--very-sensitive` for divergent sequences
2. **TaxonKit**: Keep taxdump on SSD, use appropriate thread count
3. **InterProScan**: Enable precalculated matches (`-pa`), select specific analyses with `-appl`
4. **eggNOG-mapper**: Use `--dbmem` on high-RAM systems, set appropriate `--tax_scope`

## Database Requirements

### DIAMOND
- **NCBI nr**: ~100-200GB (DIAMOND format)
- **Custom databases**: Variable size
- **Update frequency**: Monthly recommended

### TaxonKit
- **NCBI taxdump**: ~500MB
- **Files needed**: nodes.dmp, names.dmp, merged.dmp, delnodes.dmp
- **Update frequency**: Monthly recommended

### InterProScan
- **InterPro data**: ~30-50GB
- **Components**: Multiple signature databases
- **Update frequency**: Quarterly recommended

### eggNOG-mapper
- **eggNOG database**: ~100GB+
- **Taxonomic-specific**: Variable (10-50GB per scope)
- **Update frequency**: Yearly recommended

## Common Issues and Solutions

### DIAMOND
- **Out of memory**: Reduce `--block-size`, increase `--index-chunks`
- **Slow performance**: Use faster sensitivity mode, reduce `--max-target-seqs`

### TaxonKit
- **Missing TaxIDs**: Update taxdump files, handle with `-F` flag
- **Slow processing**: Increase thread count, check disk I/O

### InterProScan
- **Memory errors**: Increase Java heap size in interproscan.properties
- **Timeout issues**: Split input into smaller batches

### eggNOG-mapper
- **Database download fails**: Use `--resume` flag, check disk space
- **Slow annotation**: Use `--sensmode fast`, enable `--dbmem`

## References

### Official Documentation
- DIAMOND: https://github.com/bbuchfink/diamond/wiki
- TaxonKit: https://bioinf.shenwei.me/taxonkit/usage/
- InterProScan: https://interproscan-docs.readthedocs.io/
- eggNOG-mapper: https://github.com/eggnogdb/eggnog-mapper

### Citations
- **DIAMOND**: Buchfink et al. (2021) Nature Methods. doi:10.1038/s41592-021-01101-x
- **TaxonKit**: Shen & Ren (2021) J Genet Genomics. doi:10.1016/j.jgg.2021.03.006
- **InterProScan**: Jones et al. (2014) Bioinformatics. doi:10.1093/bioinformatics/btu031
- **eggNOG-mapper**: Cantalapiedra et al. (2021) Mol Biol Evol. doi:10.1093/molbev/msab293

## Documentation Updates

**Last Updated**: 2026-02-01
**Documentation Version**: 1.0
**Tool Versions**: See individual files for version-specific information

For the most current information, always refer to the official documentation links provided in each tool's usage guide.

## Additional Resources

### Related Documentation
- See `../SKILL.md` for overall bio-annotation workflow
- See `../summaries/` for example use cases from recent papers
- See `../../bio-skills-references.md` for comprehensive references

### Support
For tool-specific issues, consult:
- Tool GitHub repositories (Issues section)
- Official documentation websites
- Bioconda package pages
- User communities (Biostars, Stack Overflow)
