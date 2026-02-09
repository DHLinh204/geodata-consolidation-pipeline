import dlt
from dlt.sources.rest_api import rest_api_source
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    database=os.getenv('POSTGRES_DB_PROJECT_CRAWL'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD_PROJECT_CRAWL'),
    port=os.getenv('POSTGRES_PORT_PROJECT_CRAWL')
)
cur = conn.cursor()

pipeline = dlt.pipeline(
    pipeline_name="gmap_geocode",
    destination=dlt.destinations.postgres(
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD_PROJECT_CRAWL')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT_PROJECT_CRAWL')}/{os.getenv('POSTGRES_DB_PROJECT_CRAWL')}"
    ),
    dataset_name="stagging"
)

cur.execute("SELECT id, name FROM raw.wards LIMIT 10")
addresses = cur.fetchall()

# API source
def get_geocode_data(address: str):
    return rest_api_source({
        "client": {"base_url": "https://maps.gtelmaps.vn/api/google/geocode/v1/search"},
        "resources": [{
            "name": "geocode_results",
            "endpoint": {
                "path": "",
                "params": {
                    "address": address,
                    "apikey": os.getenv("key")
                }
                # "data_selector": "results"
            }
        }]
    })


if __name__ == "__main__":
    for address_data in addresses:
        address = f"{address_data[1]}"
        try:
            data = get_geocode_data(address)
            load_info = pipeline.run(data)
            print(f"Completed {address}")
        except Exception as e:
            print(f"Failed {address}: {e}")
    
    cur.close()
    conn.close()
    
