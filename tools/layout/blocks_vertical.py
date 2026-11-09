# Blocks for the board with the vertical XT30 and USB-C (blocks.py, BLOCKS_FILE), from the routed
# 27 x 36 board. The vertical connectors stand in the top 6 mm, where the right-angle ones
# reached 9-10.6 mm down, so everything below them moves up SHIFT mm (default 2) with its own
# copper, J2 and the holes too, and the board is that much shorter (BH). The parts that sat on the
# bottom under the old connectors are placed again around the new connectors' pins
# (plan_vinc.py): the power input (Q1, F1, D1, D2, R1), the USB parts (U5, C17, R20, R21) and the
# diodes beside them (D3), and the CAN ESD clamp (D4), which Q1 now needs the room of.
import os as _os

SHIFT = float(_os.environ.get('SHIFT', '2'))
_MOVED = ['U6', 'Y1', 'C9', 'C11', 'C12', 'C13', 'C14', 'C15', 'FB1', 'JP3', 'R4',
          'U3', 'C16', 'R11', 'JP1',
          'R2', 'R3', 'D7', 'U1', 'C6', 'C4', 'C5', 'L1', 'D9',
          'J2', 'D6', 'D5', 'F2', 'H1', 'H2',
          'C1', 'C2', 'C3', 'C8', 'C10', 'C19', 'C20', 'C21', 'D10', 'JP2', 'LED1', 'LED2',
          'Q2', 'Q3', 'R5', 'R6', 'R13', 'R14', 'R15', 'R16', 'R17', 'R18', 'R19', 'R22', 'R23',
          'SW1', 'U7']
BLOCKS = {'body': dict(refs=_MOVED, rot=0, dx=0, dy=-SHIFT)}
SWAP = {'J1': ('hotswap_toolhead', 'XT30PB-2+2-M', 'XT30PB(2+2)-M.G.B', {'LCSC': 'C19268029'}),
        'J5': ('hotswap_toolhead', 'USB-C_TYPE-C-16P-LTH6.8', 'USB-C vertical (TYPE-C 16P LTH6.8)',
               {'LCSC': 'C5187468'})}
USB_KEEPOUT = None
CRTYD_PADS = {}
