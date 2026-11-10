"""Generate KiCad files for the toolhead board from design.py.

Outputs (in hardware/), for each board NAME in design.BOARDS (toolhead_usb):
  NAME.kicad_pro       project file (only if missing; copied from an existing project, for its
                       DRC severities)
  NAME.kicad_sch       schematic: every pin tied to its net with a label
  NAME.kicad_dru       custom design rules (current, clearance)
  NAME-bom-jlcpcb.csv  BOM in JLCPCB's upload format
and bom_jlcpcb.csv, the BOM for all boards together.
The boards themselves (NAME.kicad_pcb) are built and routed by tools/layout/run_usb.sh, which
makes the footprints from the schematic's netlist (tools/layout/from_netlist.py). Symbol UUIDs
are derived from the board and reference, so regenerating a schematic keeps the footprints
linked to their symbols.
"""
import csv
import json
import os
import uuid
from collections import defaultdict

import design

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hardware")
G = 2.54


def uid():
    return str(uuid.uuid4())


def root_uuid(board):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, "toolhead-root-" + board))


def symbol_uuid(board, ref):
    """Stable per board and reference: the footprint's path on the board is /<root>/<this>."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, "toolhead-" + board + "-" + ref))


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
    id(design.LDO_LAYOUT): "LDO_SOT23_5",
    id(design.USBLC6_LAYOUT): "USBLC6_2SC6",
    id(design.SOT23FET_LAYOUT): "NMOS_SOT23",
    id(design.XTAL4_LAYOUT): "XTAL_4PIN",
    id(design.BAT54S_LAYOUT): "BAT54S",
    id(design.CONN2_LAYOUT): "CONN_2",
    id(design.CONN6_LAYOUT): "CONN_6",
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


def build_schematic(board):
    name, title = design.BOARDS[board]
    lib = {}
    items = []
    placed = []  # (part, X, Y)
    sheet_w = 594
    x0, y = 15.24, 30.48
    for block in design.BLOCK_ORDER:
        parts = [p for p in design.parts(board) if p["block"] == block]
        if not parts:
            continue
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
             f"    (uuid {q(symbol_uuid(board, p['ref']))})"]
        for key, val, px, py, hide in props:
            s.append(f'    (property {q(key)} {q(val)} (at {f(X + px)} {f(Y - py)} 0) {FONT_HIDE if hide else FONT})')
        for num, *_ in pins:
            s.append(f'    (pin {q(num)} (uuid {q(uid())}))')
        s.append(f'    (instances (project {q(name)} (path {q("/" + root_uuid(board))}'
                 f' (reference {q(p["ref"])}) (unit 1))))')
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
        title + " - generated from design.py. Each pin connects through a net label.",
        "Powered by USB alone: U1 (ME6211C33, SOT-23-5: 1 VIN, 2 GND, 3 CE, 4 NC, 5 VOUT) makes 3.3 V from VBUS.",
        "Verify U6 pins against ST DS13560 (STM32G0B1 UFQFPN48 pinout) before layout.",
    ]
    for i, n in enumerate(notes):
        items.append(f'  (text {q(n)} (exclude_from_sim no) (at 15.24 {f(12.7 + i * 3.81)} 0)'
                     f' (effects (font (size 1.778 1.778)) (justify left bottom)) (uuid {q(uid())}))')

    sch = ["(kicad_sch (version 20231120) (generator \"eeschema\") (generator_version \"8.0\")",
           f"  (uuid {q(root_uuid(board))})",
           '  (paper "A2")',
           f'  (title_block (title {q(title)}) (rev "A") (company "") (comment 1 "Generated from design.py"))',
           "  (lib_symbols"]
    sch += list(lib.values())
    sch.append("  )")
    sch += items
    sch.append('  (sheet_instances (path "/" (page "1")))')
    sch.append(")")
    return "\n".join(sch) + "\n", endpoints, placed


DRU = """(version 1)
(rule "USB pair"
  (condition "A.inDiffPair('/USB_D')")
  (constraint diff_pair_gap (opt 0.2mm))
  (constraint track_width (opt 0.3mm)))
(rule "Fan current"
  (condition "A.NetName == '/VBUS' || A.NetName == '/FAN_P' || A.NetName == '/FAN_N'")
  (constraint track_width (min 0.3mm)))
"""


def build_bom(parts):
    groups = defaultdict(list)
    for p in parts:
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
    for board, (name, _) in design.BOARDS.items():
        sch, endpoints, placed = build_schematic(board)
        with open(os.path.join(OUT, name + ".kicad_sch"), "w") as fh:
            fh.write(sch)
        with open(os.path.join(OUT, name + ".kicad_dru"), "w") as fh:
            fh.write(DRU)
        pro = os.path.join(OUT, name + ".kicad_pro")
        if not os.path.exists(pro):
            # the other board's project (or the old single board's) carries the DRC severities
            # and netclasses; the layout run rewrites the netclasses
            src = [os.path.join(OUT, n + ".kicad_pro") for n in ("toolhead_logic", "toolhead_power", "toolhead")]
            # (the stack's projects are on branch `stack`; without one KiCad fills in its defaults)
            src = [f for f in src if os.path.exists(f)]
            d = json.load(open(src[0])) if src else {}
            d["meta"] = {"filename": name + ".kicad_pro", "version": d.get("meta", {}).get("version", 1)}
            d["sheets"] = [[root_uuid(board), "Root"]]
            if "schematic" in d:
                d["schematic"]["top_level_sheets"] = [
                    {"filename": name + ".kicad_sch", "name": name, "uuid": root_uuid(board)}]
            with open(pro, "w") as fh:
                json.dump(d, fh, indent=2)
        with open(os.path.join(OUT, name + "-bom-jlcpcb.csv"), "w", newline="") as fh:
            csv.writer(fh).writerows(build_bom(design.parts(board)))

        # Connectivity report
        nets = defaultdict(list)
        for p in design.parts(board):
            for pin, net in p["nets"].items():
                nets[net].append(f"{p['ref']}.{pin}")
        print(f"{name}: {len(design.parts(board))} parts, {len(nets)} nets, {len(endpoints)} pin endpoints")
        for net, pins in sorted(nets.items()):
            if len(pins) < 2:
                print("  SINGLE-PIN NET:", net, pins)
    with open(os.path.join(OUT, "bom_jlcpcb.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(build_bom(design.PARTS))
    lib_dir = os.path.join(OUT, "footprints", "hotswap_toolhead.pretty")
    os.makedirs(lib_dir, exist_ok=True)
    with open(os.path.join(OUT, "fp-lib-table"), "w") as fh:
        fh.write('(fp_lib_table\n  (version 7)\n'
                 '  (lib (name "hotswap_toolhead") (type "KiCad")'
                 ' (uri "${KIPRJMOD}/footprints/hotswap_toolhead.pretty")'
                 ' (options "") (descr "Project footprints"))\n)\n')


if __name__ == "__main__":
    main()
