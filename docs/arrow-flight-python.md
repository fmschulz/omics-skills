# Querying the JGI Lakehouse with Python Arrow Flight

The JGI Lakehouse exposes an Apache Arrow Flight endpoint in addition to the
REST API. Arrow Flight streams the whole result in a single call; the REST API
pages results 500 rows at a time, so for large result sets Arrow Flight is
dramatically faster.

Provenance:

- Last verified: 2026-08-05 (from the LBL VPN, which is required for the Flight endpoint)
- Tool version/release checked: `dremio-flight` 1.1.0 (latest release at time of writing)
- Release/source: https://pypi.org/project/dremio-flight/

## Running a query

In `dremio-flight` 1.1.0 there is no `query()` method:
`DremioFlightEndpointConnection` only exposes `connect()`. Put the SQL in the
connection args as the `query` key, then read the Flight stream returned by
`connect()`:

```python
import os
from dremio.flight.endpoint import DremioFlightEndpoint

ep = DremioFlightEndpoint({
    "hostname": "lakehouse-1.jgi.lbl.gov",
    "port": 32010,
    "tls": False,
    "username": os.environ["DREMIO_USER"],
    "password": os.environ["DREMIO_PASSWORD"],
    "query": "SELECT 1",
})
df = ep.get_reader(ep.connect()).read_pandas()
print(df)
```

## Notes

- **Port 32010 is internal.** The Flight endpoint is only reachable from the
  LBL network: it was refused from a home connection but open on the LBL VPN.
  The REST endpoint on 443 works from both on-site and external connections,
  so use the REST API when you are off-site.
- **Use `tls: False` against this host.** `large_metagenome_queries.md` shows
  `"tls": True` with a PAT against the same host and port, but `tls: True`
  fails against `lakehouse-1.jgi.lbl.gov:32010`: without `path_to_certs` it
  raises "Trusted certificates must be provided to establish a TLS
  connection", and with `path_to_certs=certifi.where()` the handshake fails
  with `SSL_ERROR_SSL: wrong version number`. Only `tls: False` worked, which
  suggests a separate TLS listener or something on-site in front of it.
- **Arrow Flight is much faster than the REST API.** The same query over
  `"gold-db-2 postgresql".gold.organism_v2` (605,885 rows) returned in
  31 seconds over Arrow Flight, but took 7 minutes 50 seconds across 1,212
  requests over the REST API, which caps results at 500 rows per page and
  returns an empty page rather than an error if you ask for more.

See [large_metagenome_queries.md](large_metagenome_queries.md) for a worked
example against the metagenome tables.
