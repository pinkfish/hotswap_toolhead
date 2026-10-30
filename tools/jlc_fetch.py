"""jlc_fetch.py - cache JLCPCB's own footprint pads for every LCSC part in the BOM.
    python3 tools/jlc_fetch.py            fetch parts missing from tools/jlc_footprints.json
    python3 tools/jlc_fetch.py --all      refetch everything
JLCPCB places each part by its EasyEDA footprint: the footprint origin is the CPL
'Mid X/Y' and its drawn orientation is rotation 0. jlc_cpl.py fits these pads onto the
board's pads to write a CPL that needs no per-part rotation fixes. Pads are stored in mm,
y up, relative to the footprint origin.
"""
import csv
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DB = os.path.join(ROOT, 'tools', 'jlc_footprints.json')
URL = 'https://lceda.cn/api/products/{}/components?version=6.4.19.5'


def fetch(code):
    req = urllib.request.Request(URL.format(code), headers={'User-Agent': 'Mozilla/5.0'})
    d = json.load(urllib.request.urlopen(req, timeout=20))['result']['packageDetail']
    s = d['dataStr']
    ox, oy = float(s['head']['x']), float(s['head']['y'])
    pads = {}
    for sh in s['shape']:
        if sh.startswith('PAD~'):
            f = sh.split('~')     # PAD~shape~x~y~w~h~layer~net~number~..., units of 10 mil, y down
            pads[f[8]] = [round((float(f[2]) - ox) * 0.254, 4), round(-(float(f[3]) - oy) * 0.254, 4)]
    return {'footprint': d['title'], 'pads': pads}


db = json.load(open(DB)) if os.path.exists(DB) else {}
codes = sorted({r['LCSC Part #'] for r in csv.DictReader(open(os.path.join(ROOT, 'hardware', 'bom_jlcpcb.csv')))
                if r['LCSC Part #']})
failed = []
for c in codes:
    if c in db and '--all' not in sys.argv:
        continue
    try:
        db[c] = fetch(c)
        print(c, db[c]['footprint'], len(db[c]['pads']), 'pads')
    except Exception as e:
        failed.append(c)
        print(c, 'failed:', e)
    time.sleep(1)
json.dump(dict(sorted(db.items())), open(DB, 'w'), indent=1)
print(len(db), 'parts cached;', 'failed: ' + ' '.join(failed) if failed else 'none failed')
