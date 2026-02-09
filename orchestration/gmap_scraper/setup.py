from setuptools import find_packages, setup

setup(
    name="gmap_scraper",
    packages=find_packages(exclude=["gmap_scraper_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
