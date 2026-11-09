"""Export DSN and inset the routing boundary so tracks keep the board-edge clearance."""
import pcbnew, sys, re
pcb = sys.argv[1]; dsn = pcb.replace('.kicad_pcb', '.dsn'); inset = 300  # um
b = pcbnew.LoadBoard(pcb)
for n in ('/+24V', '/FAN_N', '/GND', '/USB_D_P'):
    if b.FindNet(n):
        print(n, b.FindNet(n).GetNetClassName())
assert pcbnew.ExportSpecctraDSN(b, dsn)
s = open(dsn).read()
m = re.search(r'\(boundary\s*\(path pcb 0\s+([-\d.\s]+)\)', s)
v = [float(x) for x in m.group(1).split()]
xs, ys = v[0::2], v[1::2]
x0, x1, y0, y1 = min(xs) + inset, max(xs) - inset, min(ys) + inset, max(ys) - inset
path = f'(path pcb 0  {x1:g} {y0:g}  {x0:g} {y0:g}  {x0:g} {y1:g}  {x1:g} {y1:g}  {x1:g} {y0:g})'
s = s[:m.start()] + '(boundary\n      ' + path + s[m.end():]
open(dsn, 'w').write(s)
print('boundary', path)
