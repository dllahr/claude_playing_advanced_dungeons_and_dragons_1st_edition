#!/usr/bin/env bash
# Rebuild a map database from the scanned page, end to end.
#
#     ./rebuild.sh dmg
#     ./rebuild.sh b1
#     ./rebuild.sh both
#
# THE ORDER OF THESE STEPS IS LOAD-BEARING and each one was got wrong once:
#
#   1. build.py       cells and edges from the image, then the key module, then
#                     the human corrections file, which always wins.
#   2. markers.py     the secret-door detector. MUTATES the database and is NOT
#                     idempotent -- it must run on a freshly built one, never
#                     on a database it has already touched.
#   3. extents.py     assigns squares to areas. Runs AFTER markers because
#                     extents depend on which boundaries are open, and applying
#                     a secret door changes that. It clears cells.room first,
#                     so anything keyed on room membership must come after it.
#   3b. build.py apply_corrections AGAIN. markers.py MUTATES edges and will
#                     happily overwrite a human correction with a secret door --
#                     (33,13,V) was corrected to `wall` and came back `secret`.
#                     Corrections are supposed to always win, so they are
#                     re-applied after every step that can touch an edge.
#   3c. doorcheck.py  a REVIEW step, not a build step: it changes nothing, it
#                     flags door calls that look like drawn furniture and
#                     writes a contact sheet of every one. Six of B1's
#                     furnished rooms shipped fabricated doors and all six were
#                     found during play, by the player. Read the sheet.
#   3e. diagcheck.py  the same, for 45-degree walls -- rock drawn INSIDE a
#                     square, which no boundary measurement can see, so extents
#                     flood straight through it. Area 34 came out as 41 squares
#                     holding another room's markers and was found in live play
#                     with the party standing in it. Also a review step: it
#                     writes nothing, it prints the hits and the corrections
#                     they imply. Read that sheet too.
#   4. world.py       what the PARTY has done. Runs LAST because it writes
#                     cells.seen by area, which needs step 3's extents, and
#                     because build.py deletes the database at step 1 and would
#                     otherwise wipe it.
#
# Skipping step 3 leaves cells.room set on the LABEL SQUARES ONLY -- 58 squares
# out of 1196 on B1 -- which looks like success and quietly makes every
# area-scoped query wrong. That is how this script came to exist.
#
# The per-map options are measured, not guessed; mapdb/README.md has the table
# of what differs and why.
set -euo pipefail
cd "$(dirname "$0")"

B1_PDF="../modules/tsr09023 -In Search of the Unknown .pdf"
DMG_PDF="../manuals/tsr02011 - Advanced Dungeons & Dragons (Ad&D) 1St Ed - Dungeon Master'S Guide.pdf"

rebuild_dmg () {
    echo "=== DMG sample dungeon ==============================================="
    python build.py --plots
    python markers.py --db output/dmg/dmg.sqlite \
        --sheet output/dmg/images/15_markers.png --apply
    python -c "import build; build.apply_corrections('output/dmg/dmg.sqlite', 'corrections.tsv', 1)"
    python extents.py --db output/dmg/dmg.sqlite --level 1 --key dmg_key --apply
    python ../tools/world.py replay --db output/dmg/dmg.sqlite --level 1 || true
    echo "--- reachability (expect 21 unreached of 641 walkable) ---"
    python dmap.py reach output/dmg/dmg.sqlite 1 --from-room 1 | head -1
}

rebuild_b1 () {
    echo "=== B1 Quasqueton, upper level ======================================="
    # --channel r      : B1 is printed in BLUE; blue absorbs red, so the red
    #                    channel roughly doubles the ink/paper contrast
    # --t-thick 6.0    : B1's rulings are heavier than the DMG's (walls 7-18px)
    # --boxr 0.50      : B1 draws doors about half again the DMG's size
    python build.py --pdf "$B1_PDF" --page 1 --channel r --t-thick 6.0 \
        --boxr 0.50 --key b1_key --corrections b1_corrections.tsv \
        --db output/b1/b1.sqlite --level 1 \
        --name "B1 Quasqueton, upper level" --images output/b1/images
    # --key none: B1 has no MARKERS block; the detector proposes them.
    # --from-cell 16 1: just inside the ENTRANCE, printed across (15,0)-(17,0).
    python markers.py --db output/b1/b1.sqlite --key none --pdf "$B1_PDF" \
        --page 1 --from-cell 16 1 --max-off-line 0.30 \
        --sheet output/b1/images/20_markers.png --apply
    # Re-apply corrections: markers.py can overwrite them (see the header).
    python -c "import build; build.apply_corrections('output/b1/b1.sqlite', 'b1_corrections.tsv', 1)"
    python extents.py --db output/b1/b1.sqlite --level 1 --key b1_key --apply
    # 3d. Corrections a THIRD time. extents.py CLEARS cells.room and recomputes
    #     it, so every `member` row -- the hand-assigned squares that express
    #     B1's diagonal-walled rooms -- is wiped unless re-applied after it.
    python -c "import build; build.apply_corrections('output/b1/b1.sqlite', 'b1_corrections.tsv', 1)"
    # `|| echo` IS LOAD-BEARING. This script runs under `set -euo pipefail`, and
    # world.py replay EXITS 1 whenever any log row fails to match the map -- three
    # legacy rows ("entrance", "route", "west passage from (21,22)") do, always.
    # Without this the script ABORTS HERE, silently skipping the level-2 merge and
    # both review steps below, while everything it had already printed looked fine.
    # That is exactly how the lower level went missing on 2026-09-04.
    python ../tools/world.py replay --db output/b1/b1.sqlite --level 1 \
        || echo '*** world.py replay exited nonzero (unmatched log rows) -- CONTINUING ***'

    # 3e. THE LOWER LEVEL. build.py DELETES AND RECREATES b1.sqlite, so level 2
    #     is destroyed by every run of this function and MUST be put back here.
    #     Forgetting this loses the whole lower level silently -- the level-1
    #     numbers all still check out, so nothing fails.
    echo "--- lower level: rebuild and merge ---"
    ./rebuild_b1_lv2.sh >/dev/null || { echo '*** LEVEL 2 REBUILD FAILED ***'; exit 1; }
    # NOT `sqlite3 ... < merge_lv2.sql`: the sqlite3 BINARY IS NOT ON THE PATH
    # inside the conda env (it lives in base), so that line failed SILENTLY and
    # took the whole lower level with it while every level-1 check still passed.
    # Python's sqlite3 module is always there. isolation_level=None so the
    # script's own BEGIN/COMMIT work.
    python -c "import sqlite3; c=sqlite3.connect('output/b1/b1.sqlite'); c.isolation_level=None; c.executescript(open('merge_lv2.sql').read())" \
        || { echo '*** LEVEL 2 MERGE FAILED ***'; exit 1; }
    python ../tools/world.py replay --db output/b1/b1.sqlite --level 2 || true

    echo "--- reachability (expect 6 unreached of 1197 on lv1, 0 of 923 on lv2) ---"
    python dmap.py reach output/b1/b1.sqlite 1 --from-cell 16 1 | head -1
    python dmap.py reach output/b1/b1.sqlite 2 --from-cell 20 13 | head -1
    echo "--- door review (contact sheet: output/b1/images/30_doors.png) ---"
    python doorcheck.py --pdf "$B1_PDF" --page 1 --channel r --t-thick 6.0 \
        --boxr 0.50 --key b1_key --sheet output/b1/images/30_doors.png \
        | tail -3
    # --db is READ-ONLY here, and it is what makes the output worth reading: a
    # room with the SAME number on both sides of a 45-degree wall has flooded
    # through it. Run without --brief to get the corrections each hit implies.
    echo "--- diagonal-wall review (contact sheet: output/b1/images/31_diagonals.png) ---"
    python diagcheck.py --pdf "$B1_PDF" --page 1 --channel r --t-thick 6.0 \
        --boxr 0.50 --key b1_key --db output/b1/b1.sqlite --level 1 --brief \
        --sheet output/b1/images/31_diagonals.png
}

case "${1:-both}" in
    dmg)  rebuild_dmg ;;
    b1)   rebuild_b1 ;;
    both) rebuild_dmg; echo; rebuild_b1 ;;
    *)    echo "usage: $0 [dmg|b1|both]" >&2; exit 2 ;;
esac

echo
echo "Both counts above are REGRESSION CHECKS. If either moved, something in"
echo "the pipeline changed behaviour -- find out what before playing on it."
echo
echo "B1's expected count went 5 -> 6 on 2026-08-29 and that was CORRECT: (31,22)"
echo "was only ever reachable through one of the 39 FABRICATED doors the drawn beds"
echo "put in the barracks wall. With the room corrected to its one real door, the"
echo "square is sealed -- its true way out is west into area 31, which is itself"
echo "still mis-extracted. A square reachable only through a door that is not on"
echo "the page was never reachable."
echo
echo "B1's expected count went 4 -> 5 on 2026-08-28 and that was CORRECT: (34,13)"
echo "is a rock outcrop between two lobes of area 25, 18% open with rock on all"
echo "four sides. It had only been 'reachable' because the lobe outline around it"
echo "was read as three doors. A square that is not floor should not be reached."
