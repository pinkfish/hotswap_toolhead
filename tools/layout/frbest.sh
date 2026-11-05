#!/bin/bash
# frbest.sh workdir : route toolhead.dsn with Freerouting 1.9.0 -> toolhead.ses
# 2.2.4 crashed or hung on this board (StackOverflowError in PolylineTrace.combine,
# NullPointerException from_corner); 1.9.0 is stable and deterministic, so one run is enough.
# 1.9.0 needs its GUI (it opens a window while routing); -dct 1 confirms its dialogs after 1 s
# (one held a run for 17 minutes) and -da turns off its analytics. FR_PASSES (default 60), FR_TIMEOUT s (default 1200).
. "$(dirname "$0")/env.sh"
[ -f "$FREEROUTING_JAR" ] || { echo "Freerouting jar not found: $FREEROUTING_JAR"; exit 1; }
cd "$1"; mkdir -p fr19; cp toolhead.dsn fr19/; rm -f fr19/toolhead.ses toolhead.ses
(cd fr19 && exec "$JAVA" -jar "$FREEROUTING_JAR" -de toolhead.dsn -do toolhead.ses -mp ${FR_PASSES:-60} -dct 1 -da > fr.log 2>&1) &
pid=$!
for ((t=0; t<${FR_TIMEOUT:-1200}; t+=2)); do kill -0 $pid 2>/dev/null || break; sleep 2; done
kill $pid 2>/dev/null; wait 2>/dev/null
[ -s fr19/toolhead.ses ] || { echo "Freerouting failed (no session file)"; exit 1; }
cp fr19/toolhead.ses toolhead.ses; grep -E 'Auto-routing was completed' fr19/fr.log | sed 's/.*INFO  /freerouting: /'
