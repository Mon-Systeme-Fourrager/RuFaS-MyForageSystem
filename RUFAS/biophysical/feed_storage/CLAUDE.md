# RUFAS/biophysical/feed_storage/ — feed storage subsystem

Stores harvested and purchased feed, models degradation/loss, and serves feed
to the herd.

- `feed_manager.py` — owns the feed-storage daily step + inventory.
- `storage.py` — base storage abstraction.
- `feed_storage_enum.py` — storage-type enumeration.
- Concrete stores: `silage.py`, `hay.py`, `baleage.py`, `grain.py`,
  `purchased_feed_storage.py`.

## Flow

Filled from harvest via the **crop_soil→feed_storage** connection
(`RUFAS/data_structures/crop_soil_to_feed_storage_connection.py`) and drains to
the herd via the **feed_storage→animal** connection. Feed planning /
degradation cadence is driven from `RUFAS/simulation_engine.py`
(`_execute_feed_planning`, `_is_time_to_process_feed_degradations`).

Tests: `tests/test_biophysical/test_feed_storage/`.
