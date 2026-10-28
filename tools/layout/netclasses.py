"""Write the routing net classes into a .kicad_pro.   netclasses.py src.kicad_pro dst.kicad_pro"""
import json, sys, copy
src, dst = sys.argv[1:3]
d = json.load(open(src)); ns = d['net_settings']
base = [c for c in ns['classes'] if c['name'] == 'Default'][0]
def nc(name, w, clr, via, prio, **kw):
    c = copy.deepcopy(base); c.update(name=name, track_width=w, clearance=clr, via_diameter=via[0], via_drill=via[1], priority=prio, **kw); return c
ns['classes'] = [base,
    nc('Power', 0.8, 0.3, (0.8, 0.4), 0),          # heater path, 3 A
    nc('Fan', 0.4, 0.3, (0.6, 0.3), 1),
    nc('Supply', 0.3, 0.2, (0.6, 0.3), 2),
    nc('USB', 0.3, 0.2, (0.6, 0.3), 3, diff_pair_width=0.3, diff_pair_gap=0.2)]
pats = [('Power', n) for n in ('/VIN_RAW', '/VIN_F', '/+24V', '/HEAT_N')] + \
       [('Fan', n) for n in ('/FAN_N', '/FAN_P')] + \
       [('Supply', n) for n in ('/GND', '/+3V3', '/VIN_LOGIC', '/VBUS', '/BUCK_SW')] + \
       [('USB', n) for n in ('/USB_D_P', '/USB_D_N')]
ns['netclass_patterns'] = [{'netclass': c, 'pattern': n} for c, n in pats]
json.dump(d, open(dst, 'w'), indent=2)
