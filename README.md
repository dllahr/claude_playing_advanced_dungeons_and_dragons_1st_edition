# inventory and encumbrance

conda activate advanced_dnd_1e

python tools/carry.py                     # the summary table
python tools/carry.py roster              # the per-character descriptive list
python tools/carry.py pack                # fill the strongest first
python tools/carry.py person Dave         # one person
python tools/carry.py check               # reconcile against what you own

All four take --bearers "Dave,Yrtone,Tristle" for who's actually going. pack takes --target normal|heavy|very heavy.

# offscreen agendas (what the NPCs are doing while we're away)

python tools/offscreen.py status           # every agenda: who, which loop, its next tick, and HOW MANY items are waiting. Never what they say
python tools/offscreen.py check            # validate the agendas

`status` is safe to read: it shows the task and a count of waiting news, not the news. The news itself (`offscreen.py news --who NAME`) is read when the party meets the person, so don't run that one if you want to be surprised.

