# Shared settings for the layout scripts; override any of these in the environment.
L=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
: "${KICAD_PY:=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}"
: "${KICAD_CLI:=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}"
: "${JAVA:=java}"                                   # Java 21+ (tested with Temurin 25)
: "${FREEROUTING_JAR:=$L/freerouting-1.9.0.jar}"    # not in the repo: download Freerouting 1.9.0
PY=$KICAD_PY
F() { grep -v "assert\|leak\|Debug"; }              # pcbnew's wxWidgets noise
