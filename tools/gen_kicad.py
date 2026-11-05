"""Generate KiCad 8 files for the toolhead controller from design.py.

Outputs (in ./out):
  toolhead.kicad_pro   minimal project file (only if missing)
  toolhead.kicad_sch   schematic: every pin tied to its net with a label
  toolhead.kicad_pcb   board outline, M2.5 holes, notes (footprints come in
                       with Tools > Update PCB from Schematic); only written
                       if missing, so the routed board is never overwritten
  toolhead.kicad_dru   custom design rules (current, clearance)
  place_footprints.py  run in the PCB editor's scripting console after
                       updating, to drop parts onto the floorplan
  bom_jlcpcb.csv       BOM in JLCPCB's upload format
"""
import csv
import json
import os
import uuid
from collections import defaultdict

import design

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hardware")
G = 2.54
ROOT_UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "toolhead-root"))


def uid():
    return str(uuid.uuid4())


def f(v):
    """Format a coordinate: round to 1e-4 mm, strip trailing zeros."""
    s = f"{round(v, 4):.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def snap(v, step=G):
    return round(v / step) * step


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


FONT = "(effects (font (size 1.27 1.27)))"
FONT_HIDE = "(effects (font (size 1.27 1.27)) hide)"

LAYOUT_NAMES = {
    id(design.STM32_LAYOUT): "STM32G0B1_LQFP48",
    id(design.BUCK_LAYOUT): "LMR16006_SOT23_6",
    id(design.CAN_LAYOUT): "CAN_XCVR_SON8",
    id(design.USBLC6_LAYOUT): "USBLC6_2SC6",
    id(design.FET_LAYOUT): "MOSFET_8PIN",
    id(design.SOT3_LAYOUT): "SOT23_3",
    id(design.SOT23FET_LAYOUT): "NMOS_SOT23",
    id(design.GATEDRV_LAYOUT): "GATE_DRIVER_SOT23_5",
    id(design.XTAL4_LAYOUT): "XTAL_4PIN",
    id(design.BAT54S_LAYOUT): "BAT54S",
    id(design.XT30_LAYOUT): "XT30_2P2",
    id(design.CONN2_LAYOUT): "CONN_2",
    id(design.CONN4_LAYOUT): "CONN_4",
    id(design.CONN8_LAYOUT): "CONN_8",
    id(design.USBC_LAYOUT): "USB_C_16P",
}
TWO_PIN_NAMES = {"R": ("~", "~"), "C": ("~", "~"), "L": ("~", "~"), "CP": ("+", "-"), "D": ("K", "A")}


# ---------------------------------------------------------------------------
# Symbol geometry. Each symbol is described by a list of pins:
#   (number, name, x, y, angle) in library coordinates (y up), where (x, y)
# is the pin's connection point, plus a body rectangle.
# ---------------------------------------------------------------------------
def two_pin_geometry(kind):
    half = 3.81 if kind in ("D", "CP") else 2.54
    n1, n2 = TWO_PIN_NAMES[kind]
    pins = [(1, n1, -(half + G), 0, 0), (2, n2, half + G, 0, 180)]
    body = (-half, 1.27, half, -1.27)
    return pins, body


def box_geometry(layout):
    left, right = layout
    n = max(len(left), len(right))
    longest = max([len(str(nm)) for _, nm in left] or [0]) + max([len(str(nm)) for _, nm in right] or [0])
    w = max(10.16, snap(longest * 1.0 + 6, G))
    w = snap(w, 2 * G)  # keep half-width on the 2.54 grid
    top = (n - 1) * G / 2
    pins = []
    for i, (num, nm) in enumerate(left):
        pins.append((num, nm, -w / 2 - G, top - i * G, 0))
    for i, (num, nm) in enumerate(right):
        pins.append((num, nm, w / 2 + G, top - i * G, 180))
    body = (-w / 2, top + G, w / 2, top - (n - 1) * G - G)
    return pins, body


def geometry(part):
    if part["kind"] == "box":
        return box_geometry(part["layout"])
    return two_pin_geometry(part["kind"])


def sym_name(part):
    if part["kind"] == "box":
        return LAYOUT_NAMES[id(part["layout"])]
    return {"R": "PASSIVE_2", "C": "CAP", "L": "INDUCTOR", "CP": "CAP_POL", "D": "DIODE"}[part["kind"]]


def lib_symbol(name, pins, body, show_names, ref_prefix):
    x1, y1, x2, y2 = body
    out = [f'    (symbol {q("toolhead:" + name)}']
    if not show_names:
        out.append("      (pin_names (offset 0) hide)")
    else:
        out.append("      (pin_names (offset 0.508))")
    out.append("      (exclude_from_sim no) (in_bom yes) (on_board yes)")
    out.append(f'      (property "Reference" {q(ref_prefix)} (at 0 {f(y1 + 1.27)} 0) {FONT})')
    out.append(f'      (property "Value" {q(name)} (at 0 {f(y2 - 1.27)} 0) {FONT})')
    out.append(f'      (property "Footprint" "" (at 0 0 0) {FONT_HIDE})')
    out.append(f'      (property "Datasheet" "" (at 0 0 0) {FONT_HIDE})')
    out.append(f'      (symbol {q(name + "_0_1")}')
    out.append(f"        (rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)})"
               " (stroke (width 0.254) (type default)) (fill (type background)))")
    out.append("      )")
    out.append(f'      (symbol {q(name + "_1_1")}')
    for num, nm, x, y, ang in pins:
        out.append(f'        (pin passive line (at {f(x)} {f(y)} {ang}) (length {G})'
                   f' (name {q(nm)} {FONT}) (number {q(num)} {FONT}))')
    out.append("      )")
    out.append("    )")
    return "\n".join(out)


def ref_prefix(ref):
    return "".join(c for c in ref if c.isalpha())


# ---------------------------------------------------------------------------
# Schematic
# ---------------------------------------------------------------------------
def part_extent(part):
    pins, body = geometry(part)
    labels_l = [len(part["nets"].get(num, "")) for num, _, x, _, _ in pins if x < 0]
    labels_r = [len(part["nets"].get(num, "")) for num, _, x, _, _ in pins if x > 0]
    xs = [p[2] for p in pins]
    left = min(xs) - (max(labels_l or [0]) * 1.1 + 3)
    right = max(xs) + (max(labels_r or [0]) * 1.1 + 3)
    top, bottom = body[1] + 3.5, body[3] - 3.5
    return left, right, top, bottom


def build_schematic():
    lib = {}
    items = []
    placed = []  # (part, X, Y)
    sheet_w = 594
    x0, y = 15.24, 30.48
    for block in design.BLOCK_ORDER:
        parts = [p for p in design.PARTS if p["block"] == block]
        items.append(f'  (text {q(block.upper())} (exclude_from_sim no) (at {f(x0)} {f(y)} 0)'
                     f' (effects (font (size 2.54 2.54) bold) (justify left bottom)) (uuid {q(uid())}))')
        y += 5.08
        x = x0
        row_h = 0
        for p in parts:
            l, r, t, b = part_extent(p)
            w, h = r - l, t - b
            if x + w > sheet_w - 15 and x > x0:
                x = x0
                y += row_h + 5.08
                row_h = 0
            X = snap(x - l)
            Y = snap(y + t)
            placed.append((p, X, Y))
            x = X + r + 2.54
            row_h = max(row_h, h)
        y += row_h + 10.16

    # Library symbols
    for p, _, _ in placed:
        name = sym_name(p)
        if name not in lib:
            pins, body = geometry(p)
            show = p["kind"] in ("box", "D", "CP")
            lib[name] = lib_symbol(name, pins, body, show, ref_prefix(p["ref"]))

    # Instances, labels, no-connects
    endpoints = {}  # (x, y) -> (net or None, ref.pin)
    for p, X, Y in placed:
        pins, body = geometry(p)
        props = [
            ("Reference", p["ref"], 0, body[1] + 1.27, False),
            ("Value", p["value"], 0, body[3] - 1.27, False),
            ("Footprint", p["fp"], 0, body[3] - 3.81, True),
            ("Datasheet", "", 0, 0, True),
            ("LCSC", p["lcsc"], 0, body[3] - 6.35, True),
        ]
        s = [f'  (symbol (lib_id {q("toolhead:" + sym_name(p))}) (at {f(X)} {f(Y)} 0) (unit 1)',
             f'    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp {"yes" if p["dnp"] else "no"})',
             f"    (uuid {q(uid())})"]
        for key, val, px, py, hide in props:
            s.append(f'    (property {q(key)} {q(val)} (at {f(X + px)} {f(Y - py)} 0) {FONT_HIDE if hide else FONT})')
        for num, *_ in pins:
            s.append(f'    (pin {q(num)} (uuid {q(uid())}))')
        s.append(f'    (instances (project "toolhead" (path {q("/" + ROOT_UUID)} (reference {q(p["ref"])}) (unit 1))))')
        s.append("  )")
        items.append("\n".join(s))
        for num, nm, px, py, ang in pins:
            ex, ey = round(X + px, 4), round(Y - py, 4)
            net = p["nets"].get(num)
            key = (ex, ey)
            if key in endpoints:
                raise SystemExit(f"Pin endpoint collision at {key}: {p['ref']}.{num} and {endpoints[key]}")
            endpoints[key] = (net, f"{p['ref']}.{num}")
            if net:
                if px < 0:
                    items.append(f'  (label {q(net)} (at {f(ex)} {f(ey)} 180) (fields_autoplaced yes)'
                                 f' (effects (font (size 1.27 1.27)) (justify right bottom)) (uuid {q(uid())}))')
                else:
                    items.append(f'  (label {q(net)} (at {f(ex)} {f(ey)} 0) (fields_autoplaced yes)'
                                 f' (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {q(uid())}))')
            else:
                items.append(f'  (no_connect (at {f(ex)} {f(ey)}) (uuid {q(uid())}))')

    notes = [
        "24 V CAN heater/fan controller - generated from design.py. Each pin connects through a net label.",
        "U1 is TI LMR16006X (SOT-23-6): pins 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW. D9 is its catch diode.",
        "J1 uses hotswap_toolhead:XT30PW-2+2-M: put the SnapEDA (or LCSC C19268030) footprint in footprints/hotswap_toolhead.pretty under that name.",
        "U3 pin 5 is TCAN3414 SHDN: left open (internal pull-down keeps the transceiver on).",
        "Verify U6 pins against ST DS13560 (STM32G0B1 LQFP-48 pinout) before layout.",
    ]
    for i, n in enumerate(notes):
        items.append(f'  (text {q(n)} (exclude_from_sim no) (at 15.24 {f(12.7 + i * 3.81)} 0)'
                     f' (effects (font (size 1.778 1.778)) (justify left bottom)) (uuid {q(uid())}))')

    sch = ["(kicad_sch (version 20231120) (generator \"eeschema\") (generator_version \"8.0\")",
           f"  (uuid {q(ROOT_UUID)})",
           '  (paper "A2")',
           '  (title_block (title "24V CAN heater/fan controller") (rev "A") (company "") (comment 1 "Generated from design.py"))',
           "  (lib_symbols"]
    sch += list(lib.values())
    sch.append("  )")
    sch += items
    sch.append('  (sheet_instances (path "/" (page "1")))')
    sch.append(")")
    return "\n".join(sch) + "\n", endpoints, placed


# ---------------------------------------------------------------------------
# PCB starter
# ---------------------------------------------------------------------------
OX, OY = 100.0, 100.0  # board origin on the PCB sheet
BW, BH = 27.0, 36.0
HOLES = {"H1": (3.2, 32.6), "H2": (23.5, 32.5)}  # M2.5 insert positions

LAYERS = """  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" power)
    (2 "In2.Cu" power)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )"""


def mounting_hole(ref, x, y):
    return f"""  (footprint "MountingHole:MountingHole_2.7mm_M2.5_Pad" (layer "F.Cu") (uuid {q(uid())}) (at {f(x)} {f(y)})
    (property "Reference" {q(ref)} (at 0 -4.3 0) (layer "F.SilkS") (uuid {q(uid())}) (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "M2.5 isolated" (at 0 4.3 0) (layer "F.Fab") (uuid {q(uid())}) (effects (font (size 1 1) (thickness 0.15))))
    (attr exclude_from_pos_files exclude_from_bom board_only)
    (fp_circle (center 0 0) (end 2.75 0) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd") (uuid {q(uid())}))
    (fp_circle (center 0 0) (end 2.75 0) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd") (uuid {q(uid())}))
    (pad "1" thru_hole circle (at 0 0) (size 5.4 5.4) (drill 2.7) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (uuid {q(uid())}))
  )"""


def build_pcb():
    notes = [
        "1. Tools > Update PCB from Schematic (F8)",
        "2. Run place_footprints.py in the scripting console",
        "3. In1 = solid GND plane, In2 = solid +24V plane; GND pours on F/B",
        "4. VIN_RAW/VIN_F pours on B.Cu; Q1 source and Q2 source via arrays",
    ]
    out = ["(kicad_pcb (version 20240108) (generator \"pcbnew\") (generator_version \"8.0\")",
           "  (general (thickness 1.6) (legacy_teardrops no))",
           '  (paper "A4")',
           '  (title_block (title "24V CAN heater/fan controller") (rev "A"))',
           LAYERS,
           "  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))",
           '  (net 0 "")',
           *(mounting_hole(ref, OX + x, OY + y) for ref, (x, y) in HOLES.items()),
           f"  (gr_rect (start {f(OX)} {f(OY)}) (end {f(OX + BW)} {f(OY + BH)}) (stroke (width 0.1) (type default))"
           f' (fill none) (layer "Edge.Cuts") (uuid {q(uid())}))']
    for i, n in enumerate(notes):
        out.append(f'  (gr_text {q(n)} (at {f(OX)} {f(OY - 12 + i * 2.2)} 0) (layer "Cmts.User") (uuid {q(uid())})'
                   ' (effects (font (size 1.2 1.2) (thickness 0.15)) (justify left bottom)))')
    out.append(")")
    return "\n".join(out) + "\n"


# Floorplan (board-relative mm, origin top-left; rot in degrees; side F/B).
# Taken from the routed board: connectors (J2 centred on the bottom edge), RESET, the BOOT
# pads and their resistor R4, LEDs and R5/R6, C1, JP1/JP2, the heater FET, its gate driver U7 and
# pull-down R14, the fan FET Q3 and R15/R16, the fan PTC F2, the 24 V and 3.3 V bulk ceramics
# (C2, C3, C8), the TH_ADC clamp D6, R11, R18, R22, R23 and C20 on top; everything else on
# the bottom.
FLOORPLAN = {
    "C1": (15.75, 15.9, 0, "F"), "C2": (24.8, 21.35, 0, "F"), "C3": (6.6, 28.8, 0, "F"),
    "C4": (29.3, 20.9, 90, "B"), "C5": (26.4, 23.2, 180, "B"), "C6": (23.6, 20.3, -90, "B"),
    "C8": (24.8, 18.6, 0, "F"), "C9": (18.9, 19.93, -90, "B"), "C10": (4, 31, 0, "B"),
    "C11": (19.92, 19.98, -90, "B"), "C12": (20.94, 19.98, -90, "B"), "C13": (18.9, 22.3, -90, "B"),
    "C14": (14.1, 21.9, 90, "B"), "C15": (13.95, 19.1, -90, "B"), "C16": (9.9, 20.7, 0, "B"),
    "C17": (25, 3, 0, "B"), "C19": (11, 22.4, 180, "B"), "C20": (5.6, 19.95, 0, "F"),
    "C21": (29.3, 27.4, 180, "B"),
    "D1": (18, 4.6, 90, "B"), "D2": (3.45, 2.75, 0, "B"), "D3": (25.4, 11, 180, "B"),
    "D4": (9, 14.3, 90, "B"), "D5": (16.75, 31.1, 90, "B"), "D6": (11.8, 21.5, 0, "F"),
    "D7": (26.4, 16.45, 180, "B"), "D9": (23, 31.5, -90, "B"), "D10": (29.45, 26.05, 180, "B"), "F1": (14.7, 4.6, 90, "B"),
    "F2": (17.4, 21.5, 0, "F"), "FB1": (21.96, 19.98, 90, "B"), "J1": (8.4, 7.27, 180, "F"),
    "J2": (19.25, 24.9, -90, "F"), "J5": (25, 3.65, 180, "F"), "JP1": (9.6, 16.6, 90, "F"),
    "JP2": (4.8, 33, 0, "F"), "JP3": (21.2, 11.9, 0, "F"), "L1": (25.6, 26.8, 0, "B"),
    "LED1": (24.55, 11, 0, "F"), "LED2": (24.55, 13, 0, "F"), "Q1": (9.7, 3.9, 0, "B"),
    "Q2": (24.2, 26.4, 180, "F"), "Q3": (7.2, 24.6, 0, "F"), "R1": (1.5, 6, 90, "B"),
    "R2": (25.9, 13.3, 0, "B"), "R3": (25.9, 14.4, 180, "B"), "R4": (21.85, 14.2, -90, "F"),
    "R5": (26.7, 10.9, 90, "F"), "R6": (26.7, 13.5, 90, "F"), "R11": (9.6, 12.95, 90, "F"),
    "R13": (30, 24.2, -90, "B"), "R14": (27.67, 20.5, 90, "F"), "R15": (3.5, 23.4, 0, "F"),
    "R16": (3.5, 24.8, 0, "F"), "R17": (9.4, 23.6, 0, "B"), "R18": (2, 28.6, 90, "F"),
    "R19": (12.65, 22.6, 90, "B"), "R20": (27.9, 4.5, 90, "B"), "R21": (22.1, 4.5, 90, "B"),
    "R22": (1.4, 19.95, 0, "F"), "R23": (3.5, 19.95, 0, "F"), "SW1": (29, 13.4, 90, "F"),
    "U1": (25.9, 20.3, -90, "B"), "U3": (9.05, 18.2, 180, "B"), "U5": (25, 7.2, 90, "B"),
    "U6": (18.8, 14.1, 90, "B"), "U7": (28.2, 26.56, 90, "F"), "Y1": (16.5, 20.9, -90, "B"),
}


def build_place_script():
    staging = {}
    col = defaultdict(int)
    blocks = design.BLOCK_ORDER
    for p in design.PARTS:
        if p["ref"] in FLOORPLAN:
            continue
        b = blocks.index(p["block"])
        i = col[b]
        col[b] += 1
        staging[p["ref"]] = (BW + 8 + i * 4.0, b * 5.0, 0, "F")
    plan = {**FLOORPLAN, **staging}
    lines = [
        '"""Place footprints on the floorplan from the design spec.',
        "",
        "Run in KiCad's PCB editor: Tools > Scripting Console, then",
        "    exec(open('/path/to/place_footprints.py').read())",
        "Parts in FLOORPLAN go onto the board; the remaining passives are",
        "staged in a grid to the right of the board, grouped by function.",
        '"""',
        "import pcbnew",
        "",
        f"OX, OY = {OX}, {OY}",
        "PLAN = {",
    ]
    for ref in sorted(plan, key=lambda r: (r not in FLOORPLAN, r)):
        lines.append(f"    {ref!r}: {plan[ref]!r},")
    lines += [
        "}",
        "",
        "board = pcbnew.GetBoard()",
        "missing = []",
        "for ref, (x, y, rot, side) in PLAN.items():",
        "    fp = board.FindFootprintByReference(ref)",
        "    if fp is None:",
        "        missing.append(ref)",
        "        continue",
        "    pos = pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))",
        "    if (side == 'B') != fp.IsFlipped():",
        "        fp.Flip(fp.GetPosition(), False)",
        "    fp.SetPosition(pos)",
        "    fp.SetOrientationDegrees(rot)",
        "pcbnew.Refresh()",
        "print('Placed', len(PLAN) - len(missing), 'footprints; not found:', missing)",
    ]
    return "\n".join(lines) + "\n"


DRU = """(version 1)
(rule "High-current nets"
  (condition "A.NetName == '/VIN_RAW' || A.NetName == '/VIN_F' || A.NetName == '/+24V' || A.NetName == '/HEAT_N'")
  (constraint track_width (min 0.8mm) (opt 3mm)))
(rule "24 V clearance"
  (condition "A.NetName == '/VIN_RAW' || A.NetName == '/VIN_F' || A.NetName == '/+24V' || A.NetName == '/HEAT_N' || A.NetName == '/FAN_N' || A.NetName == '/FAN_P'")
  (constraint clearance (min 0.3mm)))
(rule "USB pair"
  (condition "A.inDiffPair('/USB_D')")
  (constraint diff_pair_gap (opt 0.2mm))
  (constraint track_width (opt 0.3mm)))
"""


def build_bom():
    groups = defaultdict(list)
    for p in design.PARTS:
        if p["dnp"] or p["fp"] == design.FP["SJ"]:   # solder jumpers are bare copper: nothing to place
            continue
        key = (p["value"], p["fp"].split(":")[-1] if p["fp"] else "ASSIGN", p["lcsc"])
        groups[key].append(p["ref"])
    rows = [["Comment", "Designator", "Footprint", "LCSC Part #"]]
    for (val, fp, lcsc), refs in sorted(groups.items()):
        rows.append([val, ",".join(sorted(refs, key=lambda r: (ref_prefix(r), int("".join(c for c in r if c.isdigit()) or 0)))), fp, lcsc])
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    sch, endpoints, placed = build_schematic()
    with open(os.path.join(OUT, "toolhead.kicad_sch"), "w") as fh:
        fh.write(sch)
    # the PCB and project hold the routed board and its netclasses: starter only
    pcb = os.path.join(OUT, "toolhead.kicad_pcb")
    if not os.path.exists(pcb):
        with open(pcb, "w") as fh:
            fh.write(build_pcb())
    with open(os.path.join(OUT, "toolhead.kicad_dru"), "w") as fh:
        fh.write(DRU)
    with open(os.path.join(OUT, "place_footprints.py"), "w") as fh:
        fh.write(build_place_script())
    pro = {"meta": {"filename": "toolhead.kicad_pro", "version": 1},
           "sheets": [[ROOT_UUID, "Root"]]}
    if not os.path.exists(os.path.join(OUT, "toolhead.kicad_pro")):
        with open(os.path.join(OUT, "toolhead.kicad_pro"), "w") as fh:
            json.dump(pro, fh, indent=2)
    lib_dir = os.path.join(OUT, "footprints", "hotswap_toolhead.pretty")
    os.makedirs(lib_dir, exist_ok=True)
    with open(os.path.join(OUT, "fp-lib-table"), "w") as fh:
        fh.write('(fp_lib_table\n  (version 7)\n'
                 '  (lib (name "hotswap_toolhead") (type "KiCad")'
                 ' (uri "${KIPRJMOD}/footprints/hotswap_toolhead.pretty")'
                 ' (options "") (descr "Project footprints: XT30PW(2+2)-M"))\n)\n')
    with open(os.path.join(OUT, "bom_jlcpcb.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(build_bom())

    # Connectivity report
    nets = defaultdict(list)
    for p in design.PARTS:
        for pin, net in p["nets"].items():
            nets[net].append(f"{p['ref']}.{pin}")
    print(f"{len(design.PARTS)} parts, {len(nets)} nets, {len(endpoints)} pin endpoints")
    for net, pins in sorted(nets.items()):
        if len(pins) < 2:
            print("  SINGLE-PIN NET:", net, pins)


if __name__ == "__main__":
    main()
