#!/usr/bin/env bash
# Rebuild B1 Quasqueton LOWER level (level 2) into its OWN database.
# Mirrors rebuild.sh's rebuild_b1 step order exactly; never touches b1.sqlite.
set -euo pipefail
cd "/opt/dlahr/fun_and_games/DND/advanced dungeons and dragons 1e/mapdb"
B1_PDF="../modules/tsr09023 -In Search of the Unknown .pdf"
DB=output/b1/b1_lv2.sqlite
CORR=b1_lv2_corrections.tsv

python build.py --pdf "$B1_PDF" --page 2 --channel r --t-thick 6.0 \
    --boxr 0.42 --key b1_lv2_key --corrections "$CORR" \
    --db "$DB" --level 2 \
    --name "B1 Quasqueton, lower level" --images output/b1/images_lv2
python markers.py --db "$DB" --key none --pdf "$B1_PDF" \
    --page 2 --from-cell 20 13 --max-off-line 0.30 \
    --sheet output/b1/images_lv2/20_markers.png --apply
python -c "import build; build.apply_corrections('$DB', '$CORR', 2)"
python extents.py --db "$DB" --level 2 --key b1_lv2_key --apply
python -c "import build; build.apply_corrections('$DB', '$CORR', 2)"
echo "--- reachability from the level-1 stairs at (20,13) ---"
python dmap.py reach "$DB" 2 --from-cell 20 13 | head -1
