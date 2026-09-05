-- Merge B1's LOWER level (level 2) into the main B1 database.
-- Run AFTER ./rebuild.sh b1 and ./rebuild_b1_lv2.sh, in that order.
--   sqlite3 output/b1/b1.sqlite < merge_lv2.sql
-- Idempotent: it deletes level 2 first, so it can be re-run after any rebuild.
ATTACH 'output/b1/b1_lv2.sqlite' AS lv2;
BEGIN;
DELETE FROM connections WHERE level = 2;
DELETE FROM edges       WHERE level = 2;
DELETE FROM cells       WHERE level = 2;
DELETE FROM room_labels WHERE level = 2;
DELETE FROM rooms       WHERE level = 2;
DELETE FROM levels      WHERE level = 2;
INSERT INTO levels      SELECT * FROM lv2.levels      WHERE level = 2;
INSERT INTO rooms       SELECT * FROM lv2.rooms       WHERE level = 2;
INSERT INTO room_labels SELECT * FROM lv2.room_labels WHERE level = 2;
INSERT INTO cells       SELECT * FROM lv2.cells       WHERE level = 2;
INSERT INTO edges       SELECT * FROM lv2.edges       WHERE level = 2;
INSERT INTO connections SELECT * FROM lv2.connections WHERE level = 2;
COMMIT;
DETACH lv2;
