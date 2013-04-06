#!./venv/bin/python

import requests
from dogpile.cache import make_region
from glob import glob
from collections import defaultdict
import csv
import json
import os

cache = make_region().configure(
    'dogpile.cache.dbm',
    arguments = {
        "filename": "/tmp/nhtg-2013-cache.bdb",
    }
)


@cache.cache_on_arguments()
def getGeometry(name):
    args = {
        "output": "js",
        "key": file("mysociety.key").read().strip(),
        "name": name,
    }
    print "Getting bounds for", name
    return requests.get("http://www.theyworkforyou.com/api/getGeometry", params=args).json()

@cache.cache_on_arguments()
def getLoc(name):
    args = {
        "format": "json",
        "q": name,
    }
    return requests.get("http://nominatim.openstreetmap.org/search", params=args).json()

def getCenter(name):
    #d = getGeometry(name)
    #if "centre_lat" in d:
    #    return d["centre_lat"], d["centre_lon"]
    #return None
    d = getLoc(name)
    if d:
        return float(d[0]["lat"]), float(d[0]["lon"])


def tryInt(n):
    try:
        return int(n)
    except:
        return -1

def ave(*n):
    l = [x for x in n if x > 0]
    if l:
        return sum(l) / len(l)


def genRichList():
    data = {}
    for fn in ["./data/TPA/Town-Hall-Rich-List-2012/1.tsv", ]:
        for line in csv.reader(file(fn), delimiter="\t"):
            try:
                region, council, name, job, d2009, d2010 = line[0:6]
                point = getCenter(council)
                d2009 = tryInt(d2009)
                d2010 = tryInt(d2010)
                da = ave(d2009, d2010)
                if da and point:
                    if council in data:
                        data[council]["val"].append(da)
                    else:
                        data[council] = {
                            "lat": point[0],
                            "lon": point[1],
                            "val": [da, ]
                        }
            except Exception as e:
                print e

    for council in data:
        data[council]["val"] = ave(*data[council]["val"])

    return data.values()


def genRoadSalt():
    data = {}
    for fn in ["./data/TPA/Road-Salt-by-council-2009-11/1.tsv", ]:
        for line in csv.reader(file(fn), delimiter="\t"):
            try:
                council, ordered_tonnes_2009 = line[0:2]
                point = getCenter(council)
                d2009 = tryInt(ordered_tonnes_2009)
                da = ave(d2009)
                if da and point:
                    if council in data:
                        data[council]["val"].append(da)
                    else:
                        data[council] = {
                            "lat": point[0],
                            "lon": point[1],
                            "val": [da, ]
                        }
            except Exception as e:
                print e

    for council in data:
        data[council]["val"] = ave(*data[council]["val"])

    return data.values()


def dict2jsonp(name, dataFunc):
    fn = "layers/%s.js" % name
    if not os.path.exists(fn):
        print "Generating", fn
        data = dataFunc()
        file(fn, "w").write("addLayer('%s', %s);" % (name, json.dumps(data, indent=4)))
    else:
        print "Already generated", fn


dict2jsonp("rich-list", genRichList)
dict2jsonp("road-salt", genRoadSalt)

