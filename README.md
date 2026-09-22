# inventory and encumbrance

conda activate advanced_dnd_1e

python tools/carry.py                     # the summary table
python tools/carry.py roster              # the per-character descriptive list
python tools/carry.py pack                # fill the strongest first
python tools/carry.py person Dave         # one person
python tools/carry.py check               # reconcile against what you own

All four take --bearers "Dave,Yrtone,Tristle" for who's actually going. pack takes --target normal|heavy|very heavy.

