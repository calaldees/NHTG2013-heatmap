#!./venv/bin/python

# imports {{{
import requests
from dogpile.cache import make_region
from glob import glob
from collections import defaultdict
import csv
import json
import os
# }}}
# geolocation {{{
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
        "q": name+", UK",
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
# }}}
# utils {{{
def tryInt(n):
    try:
        return int(n)
    except Exception:
        return None


def ave(*n):
    l = [x for x in n if x is not None]
    if l:
        return sum(l) / len(l)


def generic(filepat, parse):
    data = {}
    for fn in glob(filepat):
        for line in csv.reader(file(fn), delimiter="\t"):
            try:
                point, value = parse(line)
                if point is not None and value is not None:
                    if point in data:
                        data[point]["val"].append(value)
                    else:
                        data[point] = {
                            "lat": point[0],
                            "lon": point[1],
                            "val": [value, ]
                        }
            except Exception as e:
                print e

    for council in data:
        if isinstance(data[council]["val"], list):
            data[council]["val"] = ave(*data[council]["val"])

    return data.values()


def dict2jsonp(name, filepat, parser):
    fn = "layers/%s.js" % name
    if not os.path.exists(fn):
        print "Generating", fn
        data = generic(filepat, parser)
        file(fn, "w").write("addLayer('%s', %s);" % (name, json.dumps(data, indent=4)))
    else:
        print "Already generated", fn

# }}}


def parseRichList(line):
    region, council, name, job, d2009, d2010 = line[0:6]
    point = getCenter(council)
    d2009 = tryInt(d2009)
    d2010 = tryInt(d2010)
    return point, ave(d2009, d2010)

dict2jsonp("rich-list", "./data/TPA/Town-Hall-Rich-List-2012/1.tsv", parseRichList)


def parseRoadSaltTonnes(line):
    council, ordered_tonnes_2009 = line[0:2]
    point = getCenter(council)
    value = tryInt(ordered_tonnes_2009)
    return point, value

dict2jsonp("road-salt-tonnes", "./data/TPA/Road-Salt-by-council-2009-11/1.tsv", parseRoadSaltTonnes)


def parseRoadSaltCost(line):
    council, t09, s09, t10, s10, when, rec, cost = line[0:8]
    point = getCenter(council)
    value = tryInt(cost)
    return point, value

dict2jsonp("road-salt-emergency-cost", "./data/TPA/Road-Salt-by-council-2009-11/1.tsv", parseRoadSaltCost)


def parseAwards(line):
    region, council, name, cost = line[0:4]
    point = getCenter(council)
    value = tryInt(cost)
    return point, value

dict2jsonp("awards", "./data/TPA/Award-Ceremony-Data-2010-2011/1.tsv", parseAwards)


def parseMileageRate(line):
    council, rate, _hmrc, amount = line[0:4]
    point = getCenter(council)
    value = tryInt(rate)
    return point, value

dict2jsonp("mileage-rate", "data/TPA/Mileage-Allowances-FINAL-2008-11/1.tsv", parseMileageRate)


def parseMileageAmount(line):
    council, rate, _hmrc, amount = line[0:4]
    point = getCenter(council)
    value = tryInt(amount)
    return point, value

dict2jsonp("mileage-amount", "data/TPA/Mileage-Allowances-FINAL-2008-11/1.tsv", parseMileageAmount)

#data/TPA/Council-Pension-Deficit-ALL-07-08-and-08-09/1.tsv
#data/TPA/Council-Pension-Deficit-London-07-08-and-08-09/1.tsv
#data/TPA/Council-Spending-Pension-Payments-09-11/1.tsv
#data/TPA/Council-tax-over-last-10-years---England,-Wales-&-Scotland-Band-D/1.tsv
#data/TPA/Empty-Property-Rates---final-data/1.tsv
#data/TPA/Housing-Associations-Head-Pay-2009-11/1.tsv
#data/TPA/Local-Council-employees---number-paying-in-vs-drawing-2006-11/1.tsv
#data/TPA/Local-Councils-Middle-Management-pay-data-12.2.13/1.tsv
#data/TPA/Local-Govt-Exec-Pay-06-08/1.tsv
#data/TPA/Number-of-Bins-and-Fines-08-09-and-09-10/1.tsv
#data/TPA/pension-deficit-data-2010-2011/1.tsv
