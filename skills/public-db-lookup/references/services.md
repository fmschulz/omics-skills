# Service cards

**Last verified:** 2026-08-24
**Tool version/release checked:** UniProt REST, NCBI E-utilities, NCBI Datasets v2, MGnify API v1, InterPro API, AlphaFold DB API, STRING API, ENA Portal API; live endpoints checked 2026-08-24
**Official docs/manual:** The Docs line on each card.
**Release/source:** The Base line on each card.

One card per `--service` value. Paths are relative to the base URL. All base URLs and example commands were checked live on 2026-08-24. "Not documented" means the official docs named on the card state no request rate.

## uniprot

- Base: `https://rest.uniprot.org`
- Docs: https://www.uniprot.org/help/api
- `uniprotkb/<accession>` with `--param fields=accession,protein_name,organism_name`: one entry, returned as `summary`
- `uniprotkb/search` with `--param query=...` and `--param size=N`: `--record-path results`
- `uniref/search`, `uniparc/search`: `--record-path results`
- Rate limit: not documented. Pass `fields` to keep entries small.
- Example: `lookup --service uniprot --path uniprotkb/P04637 --param fields=accession,protein_name,organism_name --max-items 3`

## ncbi-entrez

- Base: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
- Docs: https://www.ncbi.nlm.nih.gov/books/NBK25497/
- `esearch.fcgi` with `db`, `term`, `retmode=json`: `--record-path esearchresult.idlist` (inferred)
- `esummary.fcgi` with `db`, `id`, `retmode=json`: `summary`; the records sit under `result.<uid>`
- `efetch.fcgi` with `db`, `id`, `rettype`: usually XML or text, so add `--format text`
- Rate limit: 3 requests per second without an API key, 10 with one. NCBI asks for `tool` and `email` on every request. The script reads NCBI_API_KEY, NCBI_EMAIL, and NCBI_TOOL from the environment.
- Example: `lookup --service ncbi-entrez --path esearch.fcgi --param db=taxonomy --param term=Escherichia --param retmode=json --max-items 3`

## ncbi-datasets

- Base: `https://api.ncbi.nlm.nih.gov/datasets/v2`
- Docs: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/rest-api/ and https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/api-keys/
- `genome/accession/<GCF_or_GCA>/dataset_report`: `--record-path reports` (inferred)
- `genome/taxon/<taxon>/dataset_report` with `--param page_size=N`: `--record-path reports`
- `taxonomy/taxon/<taxid>`: `--record-path taxonomy_nodes`
- `gene/id/<gene_id>`: `--record-path reports`
- Rate limit: 5 requests per second by default, 10 with an API key. Same NCBI_* environment variables as ncbi-entrez.
- Example: `lookup --service ncbi-datasets --path genome/accession/GCF_000005845.2/dataset_report --max-items 3`

## mgnify

- Base: `https://www.ebi.ac.uk/metagenomics/api/v1`
- Docs: https://docs.mgnify.org/src/docs/api.html
- `biomes` with `--param page_size=N`: `--record-path data` (inferred)
- `studies` with `--param lineage=root:Environmental:Terrestrial:Soil`: `--record-path data`
- `samples/<accession>`, `analyses/<accession>`: `summary`; the record is under `data`
- `studies/<MGYS accession>/analyses`: `--record-path data`
- Rate limit: not documented. Page size caps at 100 per the docs.
- Example: `lookup --service mgnify --path biomes --param page_size=2 --max-items 2`

## interpro

- Base: `https://www.ebi.ac.uk/interpro/api`
- Docs: https://interpro-documentation.readthedocs.io/en/latest/
- `entry/interpro/<IPR accession>`: `summary`; the entry sits under `metadata`
- `entry/interpro/protein/uniprot/<accession>` with `--param page_size=N`: `--record-path results` (inferred)
- `protein/uniprot/<accession>`: `summary`
- `entry/pfam/<PF accession>`: `summary`
- Rate limit: not documented.
- Example: `lookup --service interpro --path entry/interpro/protein/uniprot/P04637 --param page_size=2 --max-items 2`

## alphafold

- Base: `https://alphafold.ebi.ac.uk/api`
- Docs: https://alphafold.ebi.ac.uk/api-docs
- `prediction/<UniProt accession>`: top-level list, one item per model; fields include `pdbUrl`, `cifUrl`, and `paeDocUrl`
- `uniprot/summary/<accession>.json`: `summary`
- Rate limit: not documented.
- Example: `lookup --service alphafold --path prediction/P04637 --max-items 2`

## string

- Base: `https://string-db.org/api`
- Docs: https://string-db.org/help/api/
- `json/get_string_ids` with `identifiers`, `species`: top-level list
- `json/network` with `identifiers`, `species`, `limit`: top-level list
- `json/interaction_partners` with `identifiers`, `species`, `limit`: top-level list
- `json/enrichment` with `identifiers`, `species`: top-level list
- Rate limit: the docs ask callers to wait one second between calls and to send `caller_identity`.
- Example: `lookup --service string --path json/get_string_ids --param identifiers=TP53 --param species=9606 --param caller_identity=omics-skills --max-items 2`

## ena

- Base: `https://www.ebi.ac.uk/ena/portal/api`
- Docs: https://ena-docs.readthedocs.io/en/latest/retrieval/programmatic-access.html
- `search` with `result`, `query`, `fields`, `format=json`, `limit`: top-level list
- `filereport` with `accession`, `result`, `fields`, `format=json`: top-level list
- `searchFields` with `--param result=read_run` and `results`: `--format text` (tab-separated)
- Rate limit: 50 requests per second; above that the API returns HTTP 429.
- Example: `lookup --service ena --path search --param result=read_run --param query=study_accession=PRJEB1787 --param fields=run_accession,sample_accession --param format=json --param limit=2 --max-items 2`
