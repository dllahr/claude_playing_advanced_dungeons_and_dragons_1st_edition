# Named NPCs — the roster, and how they are run

> ## ⚠ THIS FILE IS NO LONGER THE RECORD OF WHAT HAPPENED
>
> **On 2026-09-11 the ~3,000 lines of session write-ups that used to live here
> moved to `campaign/sessions/day-NNN.md`** — verbatim, complete, and archived
> rather than deleted. They are the best prose in this repository and they are
> to be read for pleasure and for quotes. **They are not to be read to answer a
> question**, because reading a summary to answer a question is the single
> largest error class in this campaign.
>
> | to find out | run |
> |---|---|
> | **what somebody said or did** | **`python tools/entities.py who <name>`** — every scene, with a day and a citation |
> | **everything logged for a character** | `python tools/recall.py <name>` — wounds, rolls, money, gear |
> | **what is still open with them** | `python tools/loops.py --touching "<name>"` |
> | **who exists at all, and their aliases** | `campaign/people.tsv` · `campaign/places.tsv` |
> | **the scenes themselves** | `campaign/interactions.tsv` |
>
> **What is left here is REFERENCE**: who these people are, the standing
> obligations, how the ex-bandits are run, and the loyalty-adjustment table.
> Facts that *change* — where somebody is, whether they are well, what they are
> owed — **are events with dates and live in the logs.** *"Unanswered. He will
> not sit in the square forever"* sat in this file for **forty-three days** after
> it was answered, because it was written as a property instead of a scene.

Everything here was played at the table; **none of it is DM-side secret.**

---

## WHERE TO FIND A PERSON — index

**This file is APPEND-STRUCTURED BY DAY, so most people have two or three entries
in different places.** Search the **bold heading** given below, not the name.

| person | search for | what's there |
|---|---|---|
| **Ista** | `## ISTA` | **her full expedition sheet** — AC 8, hp 4, hand axe at −2, the lantern duty. Her earlier entry is in the *Wethersby* table |
| **Hask** | `## The four off the road`, then `### HASK PUT HIS SHARE` | stats, AC 3, the shears stake, *he will not choose in an audience* |
| **Dellie, Corm, Sarn** | `### Gear and how to run them` | the stat table for all four ex-bandits |
| **Sarn** | `## DAY 39, evening — SARN` | **the leg, the letters, and the three things he knows about waiting in the dark.** Read the LEFT OPEN block before any Sarn scene |
| **Wend** | *Wethersby* table, then `## DAY 32` | the factorship, and why three neutral rolls in one night |
| **Coll** | `## DAY 32`, then `### COLL — 99` | his authority, and the two men still owed |
| **Marrow, Sim** | `## Marrow's holding`, then `## DAY 33` | the whole thread, closed |
| **Gyll** *(= "Rell's brother")* | `### GYLL` | the restitution, and his name |
| **Ancel** | `## DAY 32`, then `### ANCEL'S FOUR NAMES` | the four buyers |
| **Bern, Toller, Ottir, Halm, Osk, Nan** | *Wethersby* table, then `## DAY 32` | |
| **who is actually travelling** | `## THE LUDBURY CARAVAN` | **check this before putting anyone in a scene** |

**Stats and hit points are NOT authoritative here — `campaign/characters.tsv` is,
and `tools/hp.py` computes the current number.** This file is the *why*.

---

## ⛔ THE WOOL VENTURE IS WEND'S. HOW IT REACHES THE TABLE.

**Set by the player out of game, 2026-09-15:** *"I want to be making as few
decisions as possible about the wool venture. I'll enjoy hearing about the
progress, and offering help if needed."*

**SHE DECIDES. THE DM NARRATES WHAT SHE DID. THE PARTY IS NOT ASKED.**

### The trigger list — ONLY these four reach the player

| reaches him | because |
|---|---|
| **The party's own purse** | it is his money, not the venture's |
| **RAISING art. 7's cap** | only the party can. They raised it 400 → 500 themselves |
| **A party member's body or days** | those are characters, not staff |
| **Dave's four** — Hask, Dellie, Corm, Sarn | he stood surety for them personally; see below |

**Everything else is hers**, and the list of what that covers is long and
deliberate: pricing, terms, wages, hiring, who grades, who writes, letters to
holders, the cart-hire agreement, Nan, Tam, Halm, Rowe, Coll's roll. **Do not put
any of it to the player, even as a courtesy.**

*(This failed twice on day 83 alone. The DM staged a yard scene with Osk in it
and asked the player what he wanted to say — a room the party never entered and
a decision they had already given away on day 80. Then he asked whether they
wanted to question Hask about his forward promises. Both were hers.)*

### The form: A REPORT BETWEEN EXPEDITIONS, not live scenes

**When the party comes back to town, Wend reports.** One block: what happened,
what she decided, what she wants if anything. **Routine business is not played
out at the table.**

The player may always ask her about anything specific, and then it is a scene.
**The default is the report.**

> **WHAT IS NOT BEING CUT IS THE NARRATION.** *"I really enjoy reading this."*
> The district is most of what is alive in this campaign. **Fewer prompts, not
> fewer words** — the cost being removed is the DM interrupting to ask, not the
> texture.

### And her loops stay VISIBLE in the briefing

About nine of the thirty-two open loops are hers. **The player was offered a
filter that would collapse them to one line in `brief.py` and turned it down**,
and his reason is the better one: *a filter is a place for something to get
quietly hidden and then forgotten*, which is the exact defect this whole repo
was rebuilt to stop. **Nine honest lines beat one line that hides nine.**

## DAVE'S TWO STANDING OBLIGATIONS

### 1. Surety — day 4, before Reeve Ottir, by name and aloud

Dave is **answerable for Hask, Dellie, Corm and Sarn** — his purse and his good
name. If any of the four offends again it lands on Dave. In exchange Ottir wrote
nothing down and tells anyone who asks that he knows all about it and it is dealt
with. **There is nothing on paper either way.**

**The condition: the four must be visibly WORKING.** Ottir's words — *"idle men in
a market town is how this starts again."* Standing, not one-off.

### 2. "Not down the hole" — day 11, to Ferd and Ged, heard by Coll and Wat

*"I'll not ask that of anybody who isn't paid to take that kind of risk."*

**Dave will not ask any of the hired men into the caves.** Entrance-to-town
hauling only. A promise, not a preference; it constrains every plan involving
them.

---

## The four off the road (ex-bandits)

Sworn off the road **whatever happens** — the condition Dave set before offering
anything. Met in area 7 of Quasqueton, expedition 4.

| name | who | notes |
|---|---|---|
| **Hask** | grey-stubbled, **41**. Leader and speaker. **A road-robber since he was 19 — twenty-two years**, but never on *this* road until a week before the party met him | Confessed to Halm's face unprompted, before any money was offered. Returned 4 of the 6 gp he took from Bern out of his own boot. Reads a road like his own handwriting. Went flat and directionless once the crisis passed — *"you keep handing me the reins and I've got nothing to steer with"* |
| **Dellie** | the woman. Spear. Sharp, says little, means it | First of the four to accept giving up the road, instantly. Decides for Hask when he can't |
| **Corm** | quiet. Hand axe. Father was a wheelwright | Asked the one question nobody could answer: *"You can vouch for us. Can you make them take it?"* Now works Bern's bench and that satisfies Ottir's condition for him indefinitely |
| **Sarn** | broken leg | Yrtone's last *cure light wounds* took the fever out of it; **Corvie** set the bone on night 3. On crutches Corm made him |
| *Kell* | **dead** | Died underground three days before the party met them; the four got the body back and buried it under stones in a stub off their own route in. **HASK HAS NEVER SAID HOW, AND THE PARTY HAS NEVER ASKED.** He will not go back down that passage and cannot be argued into it. *(How Kell died is DM-side and is in the module notes. Do not restate it here and do not let a summary assume the party knows it — a summary already did, once, and got the direction backwards.)* |

### Gear and how to run them — **REARMOURED AT LUDBURY, day 27**

**Hask and Dellie are in BANDED MAIL, bought for them at Ludbury for 180 gp the
pair** *(d6 = 3, both gladly)*. **AC 8 → AC 4.** They were standing there and it
was bought for them, not as cargo. `campaign/characters.tsv` now says 4.

**And the two large shields off Erig's armoury wall (area 29) have been GIVEN to
them** — day 28. **AC 4 → AC 3.** They were kept off the sale list for two
expeditions for exactly this. No longer salvage; they are issued kit.

| | AC | hp | melee | missile | mounted |
|---|---|---|---|---|---|
| **Hask** | **3** (banded mail + large shield) | **7** | **short sword 1-6**, or Torsat's borrowed **spear 1-6** — **no penalty on either** | **sling**, bullet **2-5**, **−2** | **yes** — the horse bought at Ludbury, ~40 gp with tack. Scouts ahead |
| **Dellie** | **3** (banded mail + large shield) | **5** | her **spear 1-6** | **sling**, bullet **2-5**, **−2** | **yes** — the light bay bought at Marchford, 25 gp + 11 gp 5 sp tack |
| **Corm** | 8 | 4 | hand axe 1-6 | — | in Wethersby |
| **Sarn** | 8 | 2 | knife 1-3 | — | in Wethersby |

**AC 3 is the party's own front-rank number.** Hask and Dellie are now armoured
exactly as well as Dave and Torsat, which is worth saying out loud in the fiction
at some point: four months ago he was robbing carters on this road in battered
leather.

**Dellie's spear and shield:** a spear is normally two hands, but 1e has no rule
forbidding a one-handed thrust and the DMG never addresses it. **Ruled: she
carries both and takes no penalty**, consistent with how Dave and Torsat are run.
Recorded so it does not get re-decided differently mid-fight.

**Damage from `rules/combat.md`** (PHB p.38): short sword 1-6 / 1-8 vs large,
spear 1-6 / 1-8 and **double when set to receive a charge**, sling bullet 2-5 /
2-7, hand axe 1-6 / 1-4, dagger-or-knife 1-4 / 1-3.

### What they need to roll

> ## SUPERSEDED — ALL THREE BECAME 1st-LEVEL CHARACTERS ON DAY 39
>
> They are no longer normal men and **no longer need hand-rolling.** They sit in
> `campaign/characters.tsv` with classes, prime requisites and proficiencies, so
> `tools/combat.py round --attack Hask:"short sword"` resolves them off the right
> matrix with the right penalties. Scores were **rolled in the open** by the
> DMG p.11 henchman method; the dice are in `rolls.tsv`.
>
> The 0-level tables they *used* to use — and the fact that they were on the
> wrong one for two expeditions — are kept in **`rules/zero-level.md`**, because
> the next NPC who joins will be 0-level too.

| | **Hask** | **Dellie** | **Ista** |
|---|---|---|---|
| **class** | **Fighter** | **Cleric** | **Thief** |
| STR | 11 | 11 | 12 |
| INT | 12 | 10 | 13 |
| WIS | 12 | **16** | 12 |
| DEX | 11 | **4** | 13 |
| CON | 10 | **6** | **3** |
| CHA | 8 | 5 | 10 |
| **AC** | 3 | **6** *(was 3 — DEX 4 costs her +3)* | 7 |
| **hp** | 7 | 5 | 4 |
| **hit die** | d10 | d8, −1/die | d6, −2/die |
| **to hit AC 3** | 17 | 17 | 18 |
| **proficiencies** | 4: short sword, spear, sling, **one open** | 2: footman's flail, sling | 2: dart, spear |
| **non-prof. penalty** | −2 | −3 | −3 |
| **prime req. bonus** | none | **+10% (WIS 16)** | none |
| **next level** | 2,000 | 1,501 | 1,251 |

**Dellie may not use edged weapons.** The cleric prohibition (PHB p.20) applies in
full — **the spear she carried for two expeditions is gone.** Flail, sling, club,
mace, staff, war hammer.

**Dellie's DEX 4 also costs −2 on every missile**, applied automatically by
`combat.py` off `rules/abilities.md`. Her sling is proficient now but still −2.

**Ista's CON 3** is the lowest score in the campaign: −2 hp per die, **system
shock 35%**, **resurrection survival 40%** — and PHB p.12 makes initial
constitution the maximum number of times she can ever be raised. **Three.**

*Why each is the class they are, and the three printed rules that left Dellie no
choice at all, is in `rules/zero-level.md`.*

### The bows are gone; the shields are still spare

**Both bows went back to Torsat and Tristle on day 12** when the party left for
Draycot. Hask and Dellie bought **slings** instead, 15 sp each with a dozen
bullets — 3 gp the pair.

**Still no helmets.**

### HASK PUT HIS SHARE BACK IN — day 27

**Dellie took her ~19 gp half-share in coin at Ludbury. Hask did not — he pooled
his into the goods going north.** Not wages, not a share of somebody else's
venture: **part-ownership of the stock, at the same risk and reward as the
party's own money.**

**Asked on day 28 which of the freight it was buying, he put it ALL IN THE
SHEARS** *(d6 = 4)* — **19 of the 136 gp tool line, near enough one part in
seven, about four pair.** Not spread across the cargo.

**But the asking landed badly — d100 = 24.** Being made to pick in front of Wend
and Fenn read to him as a test he could only fail, and his first answer was a
defensive *"Same as yours. Three in the hundred of the lot. That's the answer
that doesn't make me a fool."* He rode two hours ahead before he came back with
the real one.

> **HOW TO ASK HIM ANYTHING: he will not choose in an audience.** Give him the
> question and then give him the road. Wend saw it instantly — *"He's not wrong
> that it was a test. He's wrong about who was being tested."*

**His reason, and he never quite says it out loud:** *"I've stood in a lot of
yards at night. You get to know a holding by the look of it — what's kept up,
what's let go. A man making do with a worn pair of shears has a particular kind
of gate. I'd sooner my money went to fixing that than to spices."*

**Wend told him to his face that it is the best line on the cart**, precisely so
he could not think he had been handed a kindness. *"That wasn't why." "I know.
That's why I said it."*

Full working in `campaign/cargo_manifest.md`. **It is still only on the back of
something in Wend's hand** — for a man who gave twenty-two years to the other
side of unwritten promises, getting it into the fair copy matters more than the
sum does.

Set against his own line from the week they met — *"you keep handing me the reins
and I've got nothing to steer with"* — this is the first thing he has actually
owned. Do not make a speech about it.

**Hask and Dellie ARE in `campaign/characters.tsv` with `share=half`** — DMG p.85
halves a non-player character's experience. `earned_by: all` deliberately does
*not* include them; they must be named on awards they were present for. See
`rules/experience.md`.

---

## The four off the farms (hired on patrol)

**No crime, no surety needed, and their story checks easily** (d6=1) — Rell's name
is known and other turned-off hands are scattered about who would confirm them.

| name | who | how found |
|---|---|---|
| **Coll** | ~40. Eleven years a hired hand for **Rell** | **Day 10.** Confessed unasked that they were waiting to rob somebody and had not, only because the road was empty. Handed Dave his billhook handle-first before walking into town. **Spotted the second pair himself next morning** |
| **Wat** | 18, Coll's sister's boy, three years on the same land | With Coll. Would go anywhere; Coll is the one who asks the hard questions for him |
| **Ferd** | ~30, shepherd, off a holding eight miles the far side of town | **Day 11.** Went to ground on seeing the party. **A natural 5** — the violently-hostile band — pulled to 50 by an unarmed approach and to **129 by Dave sitting down in his mail** |
| **Ged** | ~30, Ferd's neighbour, not kin | With Ferd. *"I'd have gone down the hole and all, for a wage."* |

---

## Wethersby

| name | who | standing |
|---|---|---|
| **Halm** | carter, ~50. One cart, and the mule was his whole living | Robbed by Hask's crew. Party bought him a mule (20 gp) and paid for the cloth (5 gp). Walked out to the thicket at night to face Hask, then fetched the bonesetter for Sarn unasked. **Will not lay a complaint.** Wants a load in his cart, not just hope |
| **Bern** | joiner, ~30. Doors, stairs, cabinet work | Robbed of 6 gp and his kit, thrown in a ditch because it was heavy. Party bought a new kit (30 gp) and set him up (22 gp). **Will not go near the caves, without shame.** Teaches the party to dismantle furniture free. **Has no room for more hands** (d6=6) — one wedding commission and Corm is all he can carry |
| **Ista** | Bern's partner, steadier than he is. **→ FULL EXPEDITION SHEET at `## ISTA`, bottom of this file** | ~~Wants to come to the dungeon and has not been answered.~~ **ANSWERED day 31. She is on the expedition from day 36** — AC 8, hp 4, and the lantern is her duty. Not a fighter: no armour, no weapon, no training. Took to Bern's tools faster than Tristle did |
| **Reeve Ottir** | ~50. Pragmatic; answers to Sir Aymer, has no men | Wants no trouble and no expense. Took the surety with relief. Gave good advice on how to run the patrol and was right. **Frightened of Sir Aymer** — Wend's word, and he doesn't deny it |
| **Wend** | cloth and wool trader, off the market square | Spent a fortnight demanding the road be patrolled and somebody hanged. **Refused the party twice in private.** Came round on **day 12, before anyone spoke** — not for the money and not for the argument, but because they walked the road publicly for six days. *"I got it from watching."* Now all the way in on the wool venture. **Knows the trade cold and does NOT know where the staple went** |
| **Toller** | book and curio dealer; fences the party's salvage at full value | Priced the diary at 50 gp, then **78 gp** once Frython proved it was Zelligar's. Warned he would not be able to keep quiet. **Frython declined to sell and offered him a cut instead** — so Toller now has an arithmetic reason to say nothing, and said so |
| **Osk** | carrier. **Wethersby to Marchford and back, three days each way, every fortnight** | Met on the road, half-day 1 of the patrol. Neutral until Dave named Ottir, then **123**. Had driven the whole lonely stretch and **seen nothing in six days** — and told the market so, unprompted, naming the party. **His run ENDS at Marchford**; beyond it the load goes to other carriers and he does not know where |
| **Corvie** | bonesetter | Fetched out to Sarn by Halm at midnight. Did not ask who he was |
| **Bircher** | offered Halm 9 gp for his cart | Did not get it |
| **Nan** | dairywoman off Ferd's old holding, with a boy of 9 and a girl of 5 | Walked in on day 15 having heard there was work. Sorting fleeces in Wend's barn; her children carry water. **Ferd named her to Dave on the road and Dave said "then bring her."** |
| **two men off Ellery's** | turned off at Michaelmas | Walked in the same week. **Seven on wages now** |

---

## Draycot — day 14

| name | who | standing |
|---|---|---|
| **the two gatemen** | Sir Aymer's, and good at it | Reacted **hostile (25)** to eight armed strangers unannounced, then **69** once Dave put his hands up and confirmed the crag rumour instead of denying it — but **resolved negative: no message carried.** *"It isn't mine to carry."* The second one, unofficially and quickly, gave two routes in. Then **82** after Yrtone pointedly pretended not to have heard him |
| **Master Wace** | **steward.** Hears petitions on his days; if Wace thinks the lord wants it, the lord hears it | **His next day is the best part of a WEEK off** (d6 = 6). He reads what is put in front of him, and *"paper waits better than people do"* |
| **Father Cuddy** | **almoner**, keeps the chapel **outside the wall**. Old. Talks to anybody. In the hall most evenings and nobody minds what he says over supper | **48 on the DOORSTEP — that was his reaction to eight armed strangers, not to the evening.** *(Corrected 2026-09-06, player-caught: the party broke bread with him and **YRTONE SAID THE EVENING PRAYERS AND THE OFFICES WITH HIM**. He knows her, and knows her as a fellow religious. Do NOT run him cold at her again — the "must be drawn out" note describes a stranger at his gate, not a priest he has prayed beside.)* Full entry: `## DAY 41, evening — FATHER CUDDY` |

**What Draycot has heard about the party: d6 = 1, word HAS travelled — and d6 = 4,
it is GARBLED.** *"Six armed strangers grubbing about that old ruin past Wethersby,
and throwing money about the town."* In a hundred where the lord has not mended a
bridge in fifteen years, **a stranger with money is not a reassuring rumour.**

**Sign on the Draycot road**, half-day 2 outbound: a cold camp thirty yards off,
**four people** (1d4=4), **a fortnight old** (d6=5), made where the fire could not
be seen from the road. Hask: *"Folk travelling make their fire where they can watch
the road. These were hiding from it."* **Not his crew** — they came up the north
road nine days ago. The trouble is not confined to one road.

---

## Marrow's holding — day 16

| name | who | |
|---|---|---|
| **Marrow** | 64, biggest flock in the hundred, stone barn stuffed with **two years of fleece** — very nearly half the district's clip | Bought up Rell's ewes cheap *"because I couldn't stand to watch them go for nothing"* and became the man holding all of it. Held out on signing not for money but **for his son**. Signed at the floor with the others once Dave offered a route rather than a promise |
| **Sim** | **16**, Marrow's son | Knows that flock and that hill better than anyone alive. Forty sentences about a roof joint; none about himself. **d6 = 6: he wants to STAY and has been dreading being sent away — and he would not say it.** Asked directly, gave *"whatever father thinks is best."* **Coming to Ludbury** with the carts, framed as a journey and a job with an end date on it, and said yes before his father finished the sentence. Somebody goes up from town to cover his chores |

**Marrow has never once asked the boy what he wants** — *"I suppose I thought if
he said he wanted to stay, I'd have to let him."* He asked **Dave** to ask, because
he could not. Dave reported it straight and did not interpret it, and **that is
the first real information Marrow has had about his own son in two years.**

~~**Sim's answer is still unknown and the party knows something Marrow does not.**~~
**RESOLVED DAY 33** — Dave quoted Sim to his father word for word, Marrow asked the
boy directly for the first time in two years, and got his *"Aye."* See `## DAY 33`
below. **Marrow knows. Do not play him as though he does not.**

## Offstage — named but not yet met

| name | who | why they matter |
|---|---|---|
| **Sir Aymer** | the lord, at **DRAYCOT** — **a long day's ride** south-west, on the road the PCs first came in by | Not distant. **He simply does not come.** Ottir sees him twice a year and will not ask him for anything. **He has his own flocks and is selling his clip SOMEWHERE**, which makes him the nearest lead on the staple. The waste and the woods are his: any assart or timber licence is his to grant and nobody else's |
| **Rell** | landowner east of the farms. **Died in the spring** | Coll gave him eleven years |
| **Rell's brother** | took the land | Turned off half the hands after they got the harvest in. **Nothing was written down**, so nothing was owed. This is why Coll asks for terms before he walks anywhere |
| **Ellery** | holder | Turned off three at Michaelmas |
| **Marrow** | holder | Bought up half of Rell's flock cheap because he wouldn't watch good ewes go for nothing. **Now sits on twice as much unsellable wool as last year.** Wend says he will deal, desperate |
| **the wool buyer** | came up every summer for **twelve years** with money and two carts, and bought the district's clip standing | **Came late two summers back. Did not come at all last summer.** Nobody in Wethersby can name where he goes now. This one absence is the cause of everything |

---

## Money the party has spent on people

| | |
|---|---|
| Halm — mule 20, cloth 5 | 25 gp |
| Bern — kit 30, coin balance 2, shop and bench 22 | 54 gp |
| **total** | **79 gp** |

Funds stood at **630 gp 3 sp 25 cp** after the day-4 sale of the expedition-4 haul.

---

## THE DRAYCOT PARTY — decided in the common room, day 12

| going | staying |
|---|---|
| All six PCs | **Corm** (Bern's bench) |
| **Hask** and **Dellie** | **Sarn** (leg) |
| **Wend** — d100 = 35, +35 = 70, resolved **72 positive.** She shuts the shop for it | **Coll, Wat, Ferd, Ged** — d6 = 5 and d6 = 5, both pairs **stay** |
| **Halm and the cart** — d100 = 70, +30 = **100, enthusiastic** | **Bern, Ista** |

**Coll and Ferd both chose to stay** and the reason is the same one Coll gave on
the road: they were hired to work, they have not seen a day's work yet, and
walking three days to a lord's gate and back is not work. They want to be *seen*
earning. Let them say so.

### OTTIR REFUSED THE SUPERVISION — d100 = 42, +25 = 67, resolved 48 NEGATIVE

He will not take charge of four hired strangers, and his objection is fair rather
than obstructive:

- **He is a reeve, not a foreman.** He collects dues and keeps the peace.
- **Dave's surety covers Hask, Dellie, Corm and Sarn — NOT these four.** Ottir has
  no wish to be the man holding people nobody has pledged for.
- And the real one: **"I've no work to give them that isn't already somebody's."**
  That is the district's whole problem restated, and he is right.

**The answer is standing in the room and the party has not looked at him.**
**COLL** is the natural foreman — forty years old, eleven of them on one holding,
already the man who thinks and asks terms and counts. **Do not suggest it.**

## THE LUDBURY CARAVAN — who is actually on it

**Thirteen out of Wethersby.** Checked and pinned 2026-09-02 after I twice put
people in a scene who were five days away.

| on the road | in Wethersby |
|---|---|
| All six PCs | **Corm** — Bern's bench |
| **Hask** (scout, mounted) and **Dellie** (mounted) | **Coll** — foreman of the wool store |
| **Wend** — the trade | **Wat, Ferd, Ged** — Coll's crew |
| **Halm** — lead cart | **Sarn** — the leg |
| **Osk** — second cart, and the guide as far as Marchford | **Bern, Ista's shop** |
| **Tam** — third cart, hired in Wethersby for the trip | **Nan** and her two children |
| **Ista** — camp and cooking | |
| **Sim** — Marrow's son, 16 | |

**Picked up on the road:** **Fenn**, and his two sons, and at his holding his wife
**Bec**.

### THE COUNT — corrected 2026-09-02

**The table above enumerates FOURTEEN on the road**, not thirteen: six PCs, Hask,
Dellie, Wend, Halm, Osk, Tam, Ista, Sim. **"Thirteen out of Wethersby" is right
— Sim joined at Marrow's holding, outside the town.** So the "sixteen people" said
in play out of Ludbury was one short; it was **seventeen** with Fenn and his two
sons. Bec cooked for seventeen.

### NORTHBOUND from Fenn's holding, day 29 — **FOURTEEN**

**Fenn, Bec and the two sons stay at their holding.** The barn is paid for and
the sons are the labour on it; Fenn's teamster wage ended when the carts reached
his gate.

**On the road north: the fourteen.** Three carts (Halm, Osk, Tam), two horses
(Hask scouting ahead, Dellie), and **229 gp in a strongbox that belongs to six
other men.**

**If a name appears in a scene, check this table first.**

## Picked up on the road south — day 27-28

| name | who | standing |
|---|---|---|
| **Fenn** | ~45, four acres of **FLAX** four miles east of the Ludbury road, a day short of Ludbury. Prices iron, nails, salt and cloth from memory | His **barn burned in August** with the whole year's crop in it. Land and house intact, nothing to eat off them. Refused to walk into Ludbury with the party — *"a man who arrives with somebody is somebody's man"* — then took **paid work at a teamster's wage** (Wend insisted on the rate). **Sold the party a share of the CROP, not the land**, for a barn, seed and a winter: **90 gp from the party, 5 from Wend**, paid back in **fibre not coin**, with his right to buy out at a price set in writing |
| **Bec** | Fenn's wife | Told the whole thing in one go and believed it (97). *"There's a well behind the byre and it's good. Don't use the one by the hedge."* Cooked for sixteen on the party's flour, and nobody said a word about it |
| **Fenn's two sons** | on the carts at a shilling a day | |
| **EDE** | **the spinner**, 53, two villages from Fenn. Has spun his flax for nine years and **has had no work since his barn burned** | Reaction 36 then **56 by one point**, then **61 by one point** on Dave's offer. **Coming to Wethersby on a WAGE** — *"a stake is a thing you take when you've time to wait for it."* Keeps her cottage and the right to return. Wants **a door she can shut**. Will teach anybody who sits down. **SHE DOES NOT WEAVE** |
| **the weaver at LYDE** | ~40, wife, three children, a house. **A day off the road each way** | Will not move. *"But he might take a lad. Or two."* Unmet |
| **Tam** | third cart driver, hired in Wethersby for the trip | |

## Open — as of day 28, on the road home

- **Ista** wants to come underground. Still unanswered, and she is *on the
  caravan* — she has been cooking for sixteen for a week.
- **Zelligar's diary, Rogahn's silver plaque and the gold-leafed headboard** are
  all with **Toller** on open terms. He judges when and to whom. ~1,025 as a set,
  ~603 apart.
- **Twenty turned-off hands in the district. Eight are the party's.** Bern has no
  room, town work is thin, and Coll said the thing nobody has answered:
  *"there's twenty out there, and none of that's fixed by six of you going
  anywhere."* **The loom, Ede, and the weaver at Lyde are the answer being built.**
- ~~Nobody knows where the wool goes.~~ **ANSWERED day 14 by Father Cuddy:
  LUDBURY. Walked day 21-27. The clip sold for 1,200.**
- **~~A place for SIM.~~ CLOSED DAY 33 — DO NOT REOPEN.** Marrow discharged the apprenticeship himself, unprompted: *"I asked you for a trade because I thought the hill was worth nothing. **I was wrong about the hill.**"* **SIM STAYS ON THE HILL**, and he chose it — he rode to Ludbury with the carts, came home with them, and learned on the road what a fleece is worth. He wants to farm like his father. *(The "two years" in the day-33 record is the SILENCE between them, not time Sim spent away. He was never away. Corrected 2026-09-06, player-caught, after I nearly offered him a weaving apprenticeship at Lyde and undid the one thing in this story anybody chose freely.)*
- **Marrow has not been told his son's answer.** It resolves at Wethersby or it
  does not resolve.
- **A lad or two for the weaver at LYDE.** Offered, not sent.
- **Whether Coll, Wat, Ferd and Ged get shares as well as wages.** Never raised.


---

# ⚠ STANDING DISPOSITIONS — and MOST OF THE TIME, DO NOT ROLL AT ALL

> ## READ THIS BEFORE USING THE TABLE BELOW — revised 2026-09-08, player-caught
>
> **The DMG p.63 reaction table is a COMBAT-CHAPTER FIRST-CONTACT MECHANIC.** Its
> running heads are `COMBAT (ENCOUNTER REACTIONS)` / `COMBAT (MISSILE DISCHARGE)`;
> it sits between initiative and avoiding/parleying/missile discharge; and its
> hostile results footnote *"or morale check if appropriate."* **It is for something
> you have just met.**
>
> **So for everyone in the table below — Wend, Ottir, Toller, Halm, Cuddy, Coll,
> Sarn, Marrow, Fenn, Bern — DO NOT ROLL A REACTION IN ORDINARY CONVERSATION.**
> They have a standing disposition, and it moves **for reasons that are on the
> record, which the DM states out loud.** Roll only for a **first meeting** or a
> **first meeting ONLY. There is no step-change exception** — the DM invented one on
> 2026-09-08 and used it four times within the hour, and it is struck. **Always roll
> for unknown FACTS, on a table declared before the die.**
>
> **Rolled conversationally, Cuddy ran 102 → 6 → 53 → 5 → 71 → 81 → 25 and Wend ran
> 101 → 60 → 57 → 26 → 46 → 12 → 41 → 37 → 88 → 46. That is a d100 with a name on
> it.** Full finding in `CHECKLIST.md` and `rules/combat.md`.

## The modifier table — for the rolls that ARE called for

**The DM rolled bare d100s for sixty game days.** DMG p.63 says to adjust encounter
reactions by Charisma **and by "any applicable loyalty adjustment, as if the
creature were a henchman of the character speaking."** Nobody in this party has a
Charisma adjustment, so the DM treated the rolls as unmodified. **The loyalty half
was never applied at all**, and the player caught it:

> *"I don't think it's realistic that they would have such wild shifts in their
> response to us."*

**Full tables now cached in `rules/combat.md`.** DMG p.37 caps it: **one penalty and
one bonus maximum, the higher of each.**

## THE TABLE — add to every reaction roll with a known NPC

| NPC | standing | basis | mod |
|---|---|---|---|
| **the four ex-bandits** (Corm, +3) | party's, via surety | **Dave stood surety before the reeve by name and aloud, which kept them out of the reeve's hands** — read as *ransomed or rescued within one year* | **+15%** *(DM call on the category)* |
| **Coll** | hireling, foreman | written authority day 34, arrears paid, a roll to run — *choice gift or bonus within two months* | **+5%** |
| **Wat** | hireling | paid rider's work twice, priced fairly, entered on the books | **+5%** |
| **Ferd, Ged** | hirelings | wages where there were none | **+5%** |
| **Sarn** | hireling, clerk | put on the roll at a clerk's wage; a teacher found | **+5%** |
| **Nan** | hireling | brought in on Ferd's word, work, and her son learning his numbers | **+5%** |
| **Wend** | **partner, not hireling** | the factorship, the succession, arts. 6-8, and the money in her keeping | **+10%** *(DM CALL — she is not a hireling; extended on a record of fair dealing)* |
| **Ottir** | independent, reeve | surety satisfied, a horse found for him, and backed in the hall in front of the steward | **+10%** *(DM CALL)* |
| **Halm** | independent, carter | given the work he had been asking for since day 40 | **+5%** *(DM CALL)* |
| **Toller** | independent, dealer | traded at full value, and **Frython gave him a cut rather than sell the diary out from under him** | **+5%** *(DM CALL)* |
| **Cuddy** | independent, almoner | told everything unprompted, twice, and shown that what he said mattered | **+5%** *(DM CALL)* |
| **Marrow** | independent | the apprenticeship discharged, paid in the square, his son's question answered | **+5%** *(DM CALL)* |
| **Fenn** | independent | 90 gp for a barn, seed and a winter, with his right to buy out **in writing** | **+10%** *(DM CALL)* |
| **Ancel** | independent | a penny in the pound for three years, honoured | **+5%** *(DM CALL)* |
| **Bern** | independent | **NO MODIFIER EITHER WAY.** No book penalty fits the day-48 rupture — he was never a hireling and was not discharged. **Do not invent a number for it; the rupture is its own fact and is on the record** |
| **strangers** | — | **0%.** A man met on a road has no history with them, which is exactly why Rud, Pell and Ossery rolled where they rolled |

> ### WHAT THIS MEANS IN PRACTICE
>
> **Cuddy's 25 becomes 30. Wend's 12 becomes 22. Trebb was a stranger and stays a
> 41.** The modifier does not turn a bad day into a good one — **it stops a
> ten-year relationship reading like a first meeting**, which is precisely the
> complaint.
>
> **AND IT IS ABOUT TO GET BIGGER.** *(1)* **Alignment is unrecorded for every
> character in this campaign** and lawful good is worth **+15% on every roll in the
> game** (DMG p.37). *(2)* Any NPC the party heals with a spell jumps to **+25%**,
> and **Ista already qualifies** — four *cure light wounds* were spent on her in
> area 9.


---
