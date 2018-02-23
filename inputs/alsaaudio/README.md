General Idea
============

* ALSA's `arecord` command can be told to:
  * "Record forever" to /dev/null.
  * Be very verbose, leading it to output ~many lines/sec, including the "max peak".

Example:
```
$ arecord --device=hw:CARD=H2300,DEV=0 --channels=2 --duration=0 --format S16_LE --rate=8000 --buffer-time=200000 -vvv /dev/null  
Recording WAVE '/dev/null' : Signed 16 bit Little Endian, Rate 8000 Hz, Stereo
Hardware PCM card 1 'HP Webcam HD 2300' device 0 subdevice 0
Its setup is:
  stream       : CAPTURE
  access       : RW_INTERLEAVED
  format       : S16_LE
  subformat    : STD
  channels     : 2
  rate         : 8000
  exact rate   : 8000 (8000/1)
  msbits       : 16
  buffer_size  : 1600
  period_size  : 400
  period_time  : 50000
  tstamp_mode  : NONE
  tstamp_type  : MONOTONIC
  period_step  : 1
  avail_min    : 400
  period_event : 0
  start_threshold  : 1
  stop_threshold   : 1600
  silence_threshold: 0
  silence_size : 0
  boundary     : 1677721600
  appl_ptr     : 0
  hw_ptr       : 0
Max peak (800 samples): 0x00007ffc #################### 99%
Max peak (800 samples): 0x00000173 #                    1%
Max peak (800 samples): 0x0000006e #                    0%
Max peak (800 samples): 0x00000087 #                    0%
Max peak (800 samples): 0x0000009b #                    0%
Max peak (800 samples): 0x00000099 #                    0%
Max peak (800 samples): 0x00000098 #                    0%
Max peak (800 samples): 0x0000008d #                    0%
Max peak (800 samples): 0x0000008b #                    0%
Max peak (800 samples): 0x00000086 #                    0%
Max peak (800 samples): 0x0000007e #                    0%
Max peak (800 samples): 0x00000083 #                    0%
Max peak (800 samples): 0x00000075 #                    0%
Max peak (800 samples): 0x00000071 #                    0%
Max peak (800 samples): 0x0000006d #                    0%
Max peak (800 samples): 0x0000006d #                    0%
Max peak (800 samples): 0x0000006e #                    0%
Max peak (800 samples): 0x0000005d #                    0%
Max peak (800 samples): 0x00000056 #                    0%
Max peak (800 samples): 0x00000057 #                    0%
Max peak (800 samples): 0x00000057 #                    0%
Max peak (800 samples): 0x00000053 #                    0%
^C
$
```

Implementation
==============

* Lauch a subprocess running `arecord` with flags sourced from the settings.
* Discard the initial output (actually sent to stderr).
* Parse each incoming "max peak" line and trigger level changes.

**IMPORTANT**:
* Running `arecord` under `nice` may be a good idea (note: after having it running for a while, I felt some sluggishness on `candle2017.py` -- spawing processes, etc -- and it triggered a few *unhandled deferred* DBus related errors like "The name <player-name> was not provided by any .service files"... strange! also: may want to wrap all DBus calls in improved exception handling)
* Will need cleanup on stop!

