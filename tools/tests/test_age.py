"""Ages — and the one thing that can rot about them.

Rolled day 99 on the DMG p.12 tables, after the player caught the DM writing
that the library's thirty-year-old papers were "older than Tristle". Tristle is
an ELF and is 120.

**Ages are recorded TWICE on purpose** -- the numbers in `campaign/characters.tsv`
where the tools read them, and the same numbers in `rules/age.md`'s summary table
where a reader can see them beside their category and their citation. That is a
second copy, which is exactly the shape of every rot this project has suffered,
so the agreement between them is asserted here rather than trusted.

An age is safe to pin in a test in a way a coordinate or a quantity is not: it
is not game state that play advances. It changes only when a game YEAR passes or
something ages a character unnaturally, and either of those is a deliberate edit
that should have to come and look at this file.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import rules                                                     # noqa: E402
from tsvlog import read_tsv                                      # noqa: E402

CHARS = os.path.join(ROOT, 'campaign', 'characters.tsv')

PARTY_TABLE = "This party's ages — rolled day 99, in the open"

# DMG p.13 age categories, for the two races this party actually contains.
HUMAN = (('Young Adult', 14, 20), ('Mature', 21, 40), ('Middle Aged', 41, 60),
         ('Old', 61, 90), ('Venerable', 91, 120))
HIGH_ELF = (('Young Adult', 100, 175), ('Mature', 176, 550),
            ('Middle Aged', 551, 875), ('Old', 876, 1200),
            ('Venerable', 1201, 1600))


def chars():
    return {r['name']: r for r in read_tsv(CHARS)}


def test_every_character_has_an_age():
    """Brand went a full day of play with no stat line at all. Not again."""
    for name, r in chars().items():
        age = (r.get('age') or '').strip()
        assert age.isdigit() and int(age) > 0, (
            '%s has age=%r -- every character in the party sheet needs one'
            % (name, age))


def test_the_rules_summary_agrees_with_the_party_sheet():
    """THE SECOND COPY. This is the whole reason this file exists."""
    table = rules.find(PARTY_TABLE)
    live = chars()
    seen = set()
    for row in table['rows']:
        name = re.sub(r'[*`]', '', row[0]).strip()
        age = re.sub(r'[^0-9]', '', row[2])
        assert name in live, 'rules/age.md lists %r, not in characters.tsv' % name
        assert age == live[name]['age'].strip(), (
            '%s: rules/age.md says %s, characters.tsv says %s -- the two copies '
            'have drifted' % (name, age, live[name]['age']))
        seen.add(name)
    assert seen == set(live), (
        'rules/age.md and characters.tsv disagree on WHO is in the party: '
        'only in the sheet %s, only in the rules %s'
        % (sorted(set(live) - seen), sorted(seen - set(live))))


def test_every_age_falls_in_the_category_the_rules_claim():
    """A number and a bracket that disagree is worse than either alone."""
    table = rules.find(PARTY_TABLE)
    for row in table['rows']:
        name = re.sub(r'[*`]', '', row[0]).strip()
        age = int(re.sub(r'[^0-9]', '', row[2]))
        claimed = re.sub(r'[*`]', '', row[3]).strip()
        bands = HIGH_ELF if 'Elf' in row[1] else HUMAN
        want = [n for n, lo, hi in bands if lo <= age <= hi]
        assert want, '%s at %d falls in no category at all' % (name, age)
        assert claimed.startswith(want[0]), (
            '%s is %d, which is %s, but the table says %r'
            % (name, age, want[0], claimed))


def test_the_elf_is_not_read_off_the_human_row():
    """The error that started all this: treating an elf as short-lived.

    A 120-year-old human would be VENERABLE. Tristle is a high-elf YOUNG ADULT,
    and the gap between those two readings is the whole point.
    """
    live = chars()
    assert live['Tristle']['class'].lower().startswith('thief')
    age = int(live['Tristle']['age'])
    assert age >= 105, 'an elf thief starts at 100 + 5d6, so never under 105'
    assert age <= 130, 'and never over 130'
    human = [n for n, lo, hi in HUMAN if lo <= age <= hi]
    elf = [n for n, lo, hi in HIGH_ELF if lo <= age <= hi]
    assert human == ['Venerable'] and elf == ['Young Adult'], (human, elf)


def test_the_starting_age_tables_are_the_books_and_are_cited():
    for heading in ('Starting age — humans',
                    'Starting age — non-human characters',
                    'Age categories',
                    'The ability adjustments — and WHEN they apply'):
        t = rules.find(heading)
        assert t['source'], '%s has no *source:* line' % heading
        assert 'DMG' in t['source']


def test_a_human_fighter_starts_younger_than_any_other_human_class():
    """15 + 1d4 is the lowest base on the table, and it surprises people."""
    t = rules.find('Starting age — humans')
    bases = {}
    for row in t['rows']:
        # The table is printed in TWO column-pairs with a blank spacer
        # column between them, exactly as the DMG prints it -- so the
        # right-hand pair is rows 3 and 4, not 2 and 3.
        for cls, formula in ((row[0], row[1]), (row[3], row[4])):
            cls = re.sub(r'[*`]', '', cls).strip().lower()
            m = re.match(r'\D*(\d+)', re.sub(r'[*`]', '', formula))
            if cls and m:
                bases[cls] = int(m.group(1))
    assert bases['fighter'] == 15
    assert min(bases.values()) == 15
    assert bases['magic-user'] == 24 and bases['cleric'] == 18
