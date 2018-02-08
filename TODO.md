* Move all these TODOs into GitHub issues?
* Implement web monitoring and control.
* Improve player manager level() call handling.
* Review code for consistency (naming, etc).
* Update movie files.
* Setup PI as an access point.
* Review log messages.
* Change DBus player names:
  * Shorter to simplify logs: no need for full qualification, running a private DBus.
  * Randomized suffix to prevent name collisions from hypothetical race conditions?...
* Move player name generation to OMXPlayer itself?
* Breakdown OMXPlayer.spawn() into smaller methods?
* Improve main.py:
  * When no DBus session detected, spawn itself under a private DBus session.
  * Rename to candle2017.py?

