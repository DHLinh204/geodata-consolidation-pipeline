from dagster import Definitions, load_assets_from_modules

from gmap_scraper import assets  # noqa: TID252

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
)
