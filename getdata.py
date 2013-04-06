#!./venv/bin/python

import requests
from dogpile.cache import make_region

cache = make_region().configure(
    'dogpile.cache.dbm',
    arguments = {
        "filename": "cache.bdb",
    }
)


@cache.cache_on_arguments()
def getGeometry(name):
    args = {
        "output": "js",
        "key": file("mysociety.key").read().strip(),
        "name": name,
    }
    return requests.get("http://www.theyworkforyou.com/api/getGeometry", params=args).json()

print getGeometry("Canterbury")
