"""KiKit layout plugin for the two-board stack: both boards in one panel.
Used by tools/make_panel.sh through tools/panel.json ("code": "tools/panel_stack.py.StackLayout").
The panel source board is the logic board; "arg" is "power.kicad_pcb;units;cols". Each column
holds `units` logic/power pairs, top to bottom L, P, L, P, ...: a 2 mm gap from a logic board
down to its power board (only USB-C's 0.55 mm front overhangs there) and the layout's vspace from
a power board down to the next logic board (J2 overhangs 2.3 mm, J1 2.8 mm). Columns are hspace
apart. References get the global board number ({orig}_{n}: logic boards even, power boards odd),
nets a per-board prefix, so no two boards share a net.
"""
import pcbnew
from kikit.panelize import Origin
from kikit.plugin import LayoutPlugin
from kikit.units import mm

PAIR_GAP = 2 * mm


def size(path):
    b = pcbnew.LoadBoard(path)
    e = b.GetBoardEdgesBoundingBox()
    return e.GetWidth(), e.GetHeight()


class StackLayout(LayoutPlugin):
    def buildLayout(self, panel, inputFile, sourceArea):
        power, units, cols = self.userArg.split(';')
        units, cols = int(units), int(cols)
        (lw, lh), (pw, ph) = size(inputFile), size(power)
        w = max(lw, pw)
        start = len(panel.substrates)
        for c in range(cols):
            x = c * (w + self.hspace)
            y = 0
            for u in range(units):
                for path, h, gap in ((inputFile, lh, PAIR_GAP), (power, ph, self.vspace)):
                    panel.appendBoard(path, pcbnew.VECTOR2I(int(x), int(y + h / 2)), origin=Origin.Center,
                                      tolerance=5 * mm,
                                      netRenamer=lambda n, orig: 'Board_{}-{}'.format(n, orig),
                                      refRenamer=lambda n, orig: '{}_{}'.format(orig, n))
                    y += h + gap
        # KiKit copies one source project's design settings and netclasses into the panel and
        # refuses two sources; gen_kicad.py writes both boards' projects and rules from one
        # template, so the logic board's serve for both
        panel.sourcePaths.discard(power)
        return panel.substrates[start:]
