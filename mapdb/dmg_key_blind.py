"""The DMG key with every door fact removed -- a stand-in for an unseen map.

Used to test the marker detector honestly. It keeps only what would be
available for a fresh map before anyone has looked at it closely:

  ROOMS   -- label positions, which are OCR-able from the sheet and are not
             secrets; they are also needed to shield numerals from the rock mask.
  STREAM  -- a terrain feature described in the module text, which the DM reads
             anyway and which is not a hidden door.

It deliberately omits SECRET_EDGES, MARKERS and CONNECTIONS, so anything the
detector finds it found from the image alone.
"""
from dmg_key import ROOMS, STREAM        # noqa: F401
