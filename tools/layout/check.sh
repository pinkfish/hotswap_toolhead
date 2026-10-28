#!/bin/bash
# check.sh board.kicad_pcb : DRC summary; the full report is left in drc.json beside the board
. "$(dirname "$0")/env.sh"
out=$(dirname "$1")/drc.json; rm -f "$out"
"$KICAD_CLI" pcb drc --format json --severity-error --severity-warning --schematic-parity -o "$out" "$1" >/dev/null 2>&1
python3 - "$out" <<'PY'
import json, sys, collections
d = json.load(open(sys.argv[1]))
print(collections.Counter((v['severity'], v['type']) for v in d['violations']))
seen = collections.Counter()
for v in d['violations']:
    if v['severity'] == 'error' or v['type'] in ('via_dangling', 'track_dangling'):
        seen[(v['type'], v['description'][:80], tuple(i['description'][:45] for i in v['items']))] += 1
for k, n in seen.most_common(30):
    print(n, k)
u = d.get('unconnected_items', [])
print('unconnected', len(u), 'parity', len(d.get('schematic_parity', [])))
for x in u:
    print('  ', [(i['description'][:45], round(i['pos']['x'] - 100, 1), round(i['pos']['y'] - 100, 1)) for i in x['items']])
PY
