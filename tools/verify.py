import os, re, sys
HW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hardware")
from collections import defaultdict
import design

def parse(s):
    toks = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', s)
    stack=[[]]
    for t in toks:
        if t=='(':
            stack.append([])
        elif t==')':
            x=stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1].replace('\\"','"') if t.startswith('"') else t)
    assert len(stack)==1, "unbalanced parens"
    return stack[0][0]

def find(node,name):
    return [c for c in node if isinstance(c,list) and c and c[0]==name]

def check(board, name):
  for ext in ["kicad_sch","kicad_pcb","kicad_dru"]:
    fn=os.path.join(HW, name+"."+ext)
    if not os.path.exists(fn):
        print("missing:",name+"."+ext); continue
    txt=open(fn).read()
    if ext=="kicad_dru":
        txt="("+txt+")"
    parse(txt); print("parsed OK:",name+"."+ext)

  sch=parse(open(os.path.join(HW, name+".kicad_sch")).read())
  libs={}
  for sym in find(find(sch,'lib_symbols')[0],'symbol'):
      name=sym[1]; pins=[]
      for sub in find(sym,'symbol'):
          for pin in find(sub,'pin'):
              at=find(pin,'at')[0]; num=find(pin,'number')[0][1]
              pins.append((num,float(at[1]),float(at[2])))
      libs[name]=pins
  labels={}
  for lab in find(sch,'label'):
      at=find(lab,'at')[0]; labels[(round(float(at[1]),3),round(float(at[2]),3))]=lab[1]
  ncs={(round(float(find(n,'at')[0][1]),3),round(float(find(n,'at')[0][2]),3)) for n in find(sch,'no_connect')}
  got=defaultdict(dict); unconnected=[]
  for inst in find(sch,'symbol'):
      lib=find(inst,'lib_id')[0][1]; at=find(inst,'at')[0]; X,Y=float(at[1]),float(at[2])
      ref=[p[2] for p in find(inst,'property') if p[1]=='Reference'][0]
      for num,px,py in libs[lib]:
          key=(round(X+px,3),round(Y-py,3))
          if key in labels: got[ref][num]=labels[key]
          elif key in ncs: pass
          else: unconnected.append(f"{ref}.{num}")
  errs=0
  for p in design.parts(board):
      want={str(k):v for k,v in p["nets"].items()}
      if got[p["ref"]]!=want:
          errs+=1; print("MISMATCH",p["ref"],want,got[p["ref"]])
  print("dangling pins:",unconnected)
  print("netlist mismatches:",errs)
  return errs
# label anchors that coincide with another symbol's pin of a different net are impossible by construction (endpoint collision check)


errs=sum(check(board, name) for board, (name, _) in design.BOARDS.items())
sys.exit(1 if errs else 0)
