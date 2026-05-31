# Authoritative sources to check (by domain)

Last verified: 2026-05-30
Tool version/release checked: NCBI taxonomy/taxdump checked 2026-05-30; GTDB Release 232; ICTV MSL41; Adl et al. 2019 eukaryote framework plus UniEuk/SILVA source pages
Official docs/manual: See source URLs in each section below.
Release/source: See source URLs in each section below.

Use these as “sources of truth” when the user asks for the **most recent** taxonomy proposals, releases, or consensus statements.

Rule: for “most recent” claims, record **(authority + identifier + date)**.

---

## Bacteria + Archaea (taxonomy + nomenclature)

### NCBI Taxonomy (curated taxonomy + schema announcements)
- NCBI Taxonomy guide / overview:
  https://www.ncbi.nlm.nih.gov/sites/guide/taxonomy/
- NCBI Insights taxonomy announcements (watch for rank schema and lineage-wide changes):
  https://ncbiinsights.ncbi.nlm.nih.gov/tag/ncbi-taxonomy/

What to extract:
- dates + scope of announced changes
- rank schema changes (domain/superkingdom/kingdom/etc.)
- notes about taxid merges/deletions and compatibility

Machine-readable dumps:
- NCBI taxdump / nodes.dmp / names.dmp:
  https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz
- NCBI new_taxdump directory:
  https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/

Verified snapshot note (2026-05-30):
- The NCBI taxonomy FTP listing showed `taxdump.tar.gz` and `taxdmp.zip` modified on 2026-05-30, and `new_taxdump/` modified on 2026-05-30. Record the file timestamp and checksum from your download, not just today's date.

### GTDB (Genome Taxonomy Database) (genome-based prokaryote taxonomy)
- GTDB portal:
  https://gtdb.ecogenomic.org/
- Latest release stats (confirm current release ID and date):
  https://gtdb.ecogenomic.org/stats/
- Release 232 stats page checked 2026-05-30:
  https://gtdb.ecogenomic.org/stats/r232
- Downloads index (confirm release folders):
  https://data.gtdb.ecogenomic.org/releases/
- Latest downloads index checked 2026-05-30:
  https://data.gtdb.ecogenomic.org/releases/latest/

What to extract:
- release ID + date (e.g., “Rxx-RSyyy”)
- high-level naming changes (phyla/classes) and summary statistics
- guidance on GTDB vs NCBI mapping differences (when provided)

### ICNP / ICSP (nomenclature governance for prokaryotes)
- ICSP code page (locate current code edition and changes):
  https://the-icsp.org/index.php/code-of-nomenclatur

Optional name validity lookup:
- LPSN:
  https://lpsn.dsmz.de/

What to extract:
- official code changes affecting ranks and valid publication
- any committee statements relevant to “accepted” names vs database usage

---

## Viruses

### ICTV (International Committee on Taxonomy of Viruses)
- ICTV taxonomy portal:
  https://ictv.global/taxonomy
- Master Species List (MSL) downloads (treat as the current “ratified species list”):
  https://ictv.global/msl
- MSL41 news page checked 2026-05-30:
  https://ictv.global/news/MSL41

What to extract:
- current MSL version identifier + date
- latest “ratified changes” paper(s) and scope
- notes about binomial species naming and any rank additions/changes (realm/kingdom/etc.)

### NCBI taxonomy (virus alignment with ICTV)
- NCBI Insights taxonomy posts:
  https://ncbiinsights.ncbi.nlm.nih.gov/tag/ncbi-taxonomy/

Current ICTV snapshot checked 2026-05-30:
- ICTV current MSL page lists `ICTV_Master_Species_List_2025_MSL41.v1.xlsx`.
- ICTV MSL41 news identifies MSL41 as the 2025-2026 ICTV taxonomy release, posted 2026-03-20, with Zenodo DOI `10.5281/zenodo.19154110`.

What to extract:
- implementation dates for virus taxonomy updates in NCBI
- compatibility notes (how old names are retained as synonyms/children)

---

## Eukaryotes

### Broad eukaryote classification frameworks (consensus-style)
- Adl et al. (2019) revised eukaryote classification (ISOP context):
  https://doi.org/10.1111/jeu.12691

Follow-ups:
- When asked “is there an updated version?”, search for:
  - “Revisions to the classification, nomenclature, and diversity of eukaryotes” + newer year
  - “International Society of Protistologists” + “classification” + update/erratum

### UniEuk (community framework, especially for protists)
- UniEuk:
  https://unieuk.net/

### Downstream reference taxonomy implementations
- SILVA eukaryotic taxonomy project:
  https://beta.arb-silva.de/projects/eukaryotic-taxonomy

What to extract:
- whether UniEuk updates were incorporated (and when)
- recommended names/lineages used in environmental sequencing pipelines
