import os
import pyarrow.flight as flight

DREMIO_HOST = os.getenv("DREMIO_HOST", "lakehouse.jgi.lbl.gov")
DREMIO_PORT = os.getenv("DREMIO_PORT", "443")
DREMIO_TOKEN = os.getenv("DREMIO_PAT")


def _flight_client():
    if not DREMIO_TOKEN:
        raise ValueError("Missing DREMIO_PAT environment variable.")
    location = f"grpc+tls://{DREMIO_HOST}:{DREMIO_PORT}"
    client = flight.FlightClient(location)
    headers = [(b"authorization", f"Bearer {DREMIO_TOKEN}".encode("utf-8"))]
    options = flight.FlightCallOptions(headers=headers)
    return client, options


def execute_lakehouse_query(sql_query: str):
    if "limit" not in sql_query.lower() and "count" not in sql_query.lower():
        sql_query += " LIMIT 100"
    client, options = _flight_client()
    info = client.get_flight_info(flight.FlightDescriptor.for_command(sql_query), options)
    reader = client.do_get(info.endpoints[0].ticket, options)
    df = reader.read_all().to_pandas()
    return df.to_dict(orient="records")


def describe_table(table_path: str):
    return execute_lakehouse_query(f"DESCRIBE {table_path}")


def list_catalogs():
    return execute_lakehouse_query("SHOW SCHEMAS")
