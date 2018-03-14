Candle 2017
===========

About
-----

**Candle 2017** is a re-implementation of an [interactive art project by Nuno Godinho](https://projects.nunogodinho.com/candle), whereby a beautifully framed high quality display shows a candle burning video, against a pitch black background. Blowing into the display triggers natural candle reactions: the flame flickers more or less depending on the blowing strength and can even be fully blown out with a strong enough blow - when so, the base candle burning video is restarted and smoothly faded in after a few seconds.

Originally written in C++ using OpenFrameworks, Nuno never got it to run with acceptable performance on the desired target platform, a Raspberry Pi; it required being driven by a much more powerful and expensive system, like a Mac Mini.

This project is a Python implementation that succeeds in delivering the required performance on a Raspberry Pi.

> Heads up: there are no silver bullets here! It's not like Python on a Raspberry Pi has suddenly more performance than well written C++ code on a Mac Mini. It just takes a completely different approach, better leveraging the available resources on the smaller system.



Minimum Requirements
--------------------
* A Raspberry Pi running raspbian.
* The following raspbian packages:
  * Python 3.
  * OMXPlayer.
  * DBus.
  * git.
* Four sets of candle burning video files, that you will have to create yourself:
  * Level 0 videos: stable candle burning with no interference.
  * Level 1 videos: candle flame flickering, responding to light blowing.
  * Level 2 videos: candle flame flickering, responding to medium blowing.
  * Level 3 videos: candle flame blowing out, responding to strong blowing.
  * Any of these sets can (and should, for a more natural experience) contain multiple files: one will be selected at random from a given level, to be played when the respective interaction is triggered (the exception being level 0 videos whereby one will be selected at startup time and played continuously in a loop).

With these in place you will be able to explore **Candle 2017** and trigger candle reactions artificially, either via a web based monitoring and controlling interface or via a simpler network based control interface; for details on this see the *Using* section, below.





Full Requirements
-----------------
For full, natural interactivity, an input sensor is required. As of this writing, two types of input sensor are supported:

* The original "wind sensor", as used in the art project itself, is comprised of multiple [bend/flex sensors](https://en.wikipedia.org/wiki/Flex_sensor) integrated in the display frame assembly, wired to an arduino that, in turn, continuously delivers "bend readings" to the Raspberry Pi, via a serial USB connection: these will be bigger as the "wind blowing towards the screen" strength increases, forcing the "bend/flex sensors" to move.

* An alternative "audio sensor", much simpler and accessible, based on sound input; this requires prior setup of the ALSA subsystem such that, for example, a USB microphone or webcam audio can be used: naturally, this input sensor reacts to both directed blows and environment sound pressure/level changes.

Either input sensor is fed into an input processor, called AGD, that can be tuned in a way such that varying inputs (more/less wind or louder/softer sound) trigger the natural candle reactions by playing videos in different levels.




Optional Requirements
---------------------
As an alternative to the input sensors above, a USB HID device with some kind of analog-like input can also be used: a mouse, an analog joystick, a game pad with analog sticks are among the devices that should work.

Like both the "wind sensor" and the "audio sensor", the USB HID device input will also produce a stream of readings to be processed by AGD.




Operation Overview
------------------

At a very high level, **Candle 2017** is an interactive video player: it plays one of the existing level 0 video files in a loop, while monitoring for inputs: varying input signals then trigger the playing of level 1 to 3 videos, smoothly cross-faded with the base level 0 video, for a mostly natural video experience.

Five input types are supported:
* A "wind sensor".
* An "audio sensor".
* A USB HID analog-like device.
* A web based interface.
* A raw TCP network interface.


Of these, the last two are mostly used for testing and diagnostics, while the first two support the full natural experience: both the "wind sensor" and the "audio sensor" produce a continuous stream of numeric readings where larger numbers correspond to more wind or sound, respectively. The USB HID input sits somewhere in between, being mostly useful for testing, but delivering an analog-like experience, also producing a continuous stream of readings.

Such streams of readings, from either the "wind sensor", the "audio sensor" or the USB HID input, are handled by an internal processing component called AGD which, in turn, triggers video level playing changes, depending on its own settings.

AGD keeps track of the latest N readings (configurable) and calculates a particular form of "aggregated derivative" over those readings: whenever the calculated value rises above a given video level's configurable threshold, AGD triggers that particular video level to start playing.


An overview of the input chain is depicted below, triggering current playing video level changes:
```
    +-------------------+
    |    wind sensor    |---(bend readings)----------------+
    +-------------------+                                  |
                                                           V
    +-------------------+                             +---------+
    |    audio sensor   |---(level readings)----X     |   AGD   |
    +-------------------+                             +---------+
                                                           |
    +-------------------+                                  |
    |      USB HID      |---(analog readings)---X          |
    +-------------------+                                  |
                                                           |          *- - - - - - - - -*
    +-------------------+                                  +--------->| current playing |
    | web input/monitor |-------------------------------------------->|   video level   |
    +-------------------+                                  +--------->| change triggers |
                                                           |          *- - - - - - - - -*
    +-------------------+                                  |
    |   network input   |----------------------------------+
    +-------------------+
```

Note that AGD will only process one input, either the "wind sensor", the "audio sensor" or the USB HID input; in the example configuration above, the "wind sensor" is being used.



Installation
------------

Install the required raspbian packages:
```
$ sudo apt-get update
$ sudo apt-get install python3 python3-virtualenv omxplayer dbus git
```

If using an "audio sensor":
```
$ sudo apt-get install alsa-utils
```

Clone the repository and setup a virtual environment:
```
$ git clone https://github.com/nununo/pyVela2017
$ cd pyVela2017
$ virtualenv -p /usr/bin/python3 <venv-path-to-be-created>
$ source <venv-path-to-be-created>/bin/activate
$ pip install -r requirements.txt
```

Put the video files in place:
* The default configuration expects a directory named `videos` to be present side by side with the source directory.
* It should have four sub-directories, named `0`, `1`, `2` and  `3`, each containing the candle burning video files, as described in the *Minimum Requirements* section, above.




Configuration
-------------

Before running, putting a configuration in place that is appropriate to the environment is strictly required. For that, copy `settings-sample.json` to `settings.json` and then edit the copy, as needed.


If using an input like a "wind sensor", an "audio sensor", or a USB HID device, the `inputs` entry must be reviewed:

* If using a "wind sensor":
  * Set `inputs.arduino.enabled` to `true` and adjust the other `input.arduino.*` settings.
  * Set `inputs.agd.enabled` to `true`.
  * Set `inputs.agd.source` to `arduino`.
  * For details about building a "wind sensor", see the section *About the "wind sensor"*, below.

* If using an "audio sensor":
  * Set `inputs.audio.enabled` to `true` and adjust the other `input.audio.*` settings.
  * Set `inputs.agd.enabled` to `true`.
  * Set `inputs.agd.source` to `audio`.
  * For details about setting up and testing an "audio sensor", see the section *About the "audio sensor"*, below.

* If using a USB HID input:
  * Set `inputs.hid.enabled` to `true` and adjust the other `input.hid.*` settings.
  * Set `inputs.agd.enabled` to `true`.
  * Set `inputs.agd.source` to `hid`.
  * For details about setting up and testing a USB HID device, see the section *About USB HID devices*, below.

* About the web based input:
  * Not strictly required but its monitoring and diagnosing abilities may prove useful.
  * Review the `input.web.*` settings.

* About the network input:
  * Can be disabled.
  * If enabled, review the `input.network.*` settings.



 
Running
-------

Activate the Python virtual environment:
```
$ source <path-to-your-venv>/bin/activate
```

Change working directory to the repository root and run:
```
$ cd <path-to-repository-root>
$ python candle2017.py
```

> Optionally, make `candle2017.py` executable with `chmod u+x candle2017.py` and run it with `./candle2017.py`.


Once running:
* The Python process running `candle2017.py` should have the following child processes:
  * One `dbus-daemon` process.
  * Four `omxplayer.bin` processes.
  * One `arecord` process, if the "audio" input is included in the configuration.
* One of the videos in the videos `0` directory should be playing, in a loop.
* Log messages will be output to `stderr`; see below to learn how to adjust logging details.

Stopping:
* Hit CTRL-C on the shell that launched the program.
* Send a SIGTERM to the Python process running `candle2017.py`.

> Note: Sending a SIGTERM to the `dbus-daemon` process will also stop everything, but it is not the cleanest way to do so.


Automatic start/stop with system startup/shutdown
-------------------------------------------------

Integrating **Candle 2017** with system services, ensuring automatic startup/shutdown with the system is handled via the supplied `candle2017.service` file. Please refer to its internal comments on how to set that up.



Using
-----
As an interactive art project, using it is about interacting with it. There are currently five possible ways to interact:


**"Wind sensor" setup and interaction**

* Requires "wind sensor" to be present.
* Blow on the sensor and watch the candle react.
* *Web based monitoring and control* may be very useful.



**"Audio sensor" interaction**

* Requires the availability of an ALSA supported audio input device.
* Produce different sound levels (including blowing into the microphone) and watch the candle react.
* *Web based monitoring and control* may be very useful.



**USB HID interaction**

* Requires the availability of supported USB HID input device.
* Manipulate the device such that it generates the tracked events.
* *Web based monitoring and control* may be very useful.



**Web based monitoring and control**

* Point a web browser to http://\<raspberry-pi-IP\>:\<port\>/, where \<port> is defined by `inputs.web.port` in the configuration (defaults to 8080).
* Monitor the real-time input RAW reading value and AGD result in the top left chart.
* Observe the AGD thresholds, obtained from `inputs.agd.thresholds` in the configuration, and click them to adjust.
* Track log messages on the top right pane.
* Use the orange buttons on the bottom to manually trigger video level changes.
* Use the drop-down selectors and the green button to change logging levels at run-time.

> Important: multiple browser connections are accepted simultaneously; no effort to authenticate or limit the amount of connections is made.




**Raw TCP network control**

* Use telnet or netcat to establish a TCP connection towards the Raspberry Pi on the TCP port defined by `inputs.network.port` in the configuration (defaults to 10000).
* Send commands terminated with CRLF.
* Commands are digits terminated by CRLF that trigger the respective level videos.

Example triggering a level 1 video:

```
$ nc -c <raspberry-pi-IP> <port>
1
<CTRL-C>
$
```

> Important: multiple network connections are accepted simultaneously; no effort to authenticate or limit the amount of connections is made.



Configuration Reference
-----------------------
When running, the configuration is sourced at startup from the file `settings.json`. As its name implies, it is a JSON formatted file containing all the configurable settings.

Here's a rundown on the available settings, grouped by key:


### Environment

Defines necessary paths for spawning a private DBus daemon and OMXPlayers.

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| environment.dbus_daemon_bin      | Absolute path to the `dbus-daemon` executable.                  |
| environment.omxplayer_bin        | Absolute path to the `omxplayer.bin` executable.                |
| environment.ld_library_path      | Absolute path to the OMXPlayer required shared libraries.       |



### Logging

Sets the default logging level for each internal component. These can be changed at run-time via the web interface.

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| loglevel                         | Default log level, one of `debug`, `info`, `warn` or `error`.   |
| loglevel.*                       | Per component log level.                                        |



### Inputs

The `inputs` key is a list/array of dicts/objects containing one or more entries specifying the inputs to be used. Each such entry must have a `type` key/property, with the remaining keys/properties depending on that setting (which, for readability, are referenced below as `inputs.<type>.*`); additionally, each entry can be individually enabled/disabled depending on the boolean value of the `enabled` key/property.



### Input: "wind sensor"

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| inputs.arduino.device_file       | Absolute path to the serial device file of the "wind sensor".   |
| inputs.arduino.baud_rate         | Baud rate of the "wind sensor" communication.                   |



### Input: "audio sensor"

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| inputs.audio.nice_bin            | Absolute path to the `nice` executable.                         |
| inputs.audio.arecord_bin         | Absolute path to the `arecord` executable.                      |
| inputs.audio.device              | ALSA device as obtained from the output `arecord -L`.           |
| inputs.audio.channels            | Number of channels to "listen on".                              |
| inputs.audio.format              | Audio capture format, to be used in `arecord`'s `--format` option. |
| inputs.audio.rate                | Audio capture rate, to be used in `arecord`'s `--rate` option.  |
| inputs.audio.buffer_time         | Audio capture buffer size, to be used in `arecord`'s `--buffer-size` option. |
| inputs.audio.respawn_delay       | Delay, in seconds, to wait for `arecord` process re-spawn (no re-spawns will be attempted if negative). |



### Input: USB HID device

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| inputs.hid.device_file           | Absolute path to a USB HID input event device file.             |
| inputs.hid.reading_event_code    | The event code to track readings from (see *About USB HID devices*, below). |
| inputs.hid.reading_scale         | Reading multiplier (defaults to 1).                             |
| inputs.hid.reading_offset        | Offset added to each reading (defaults to 0).                   |
| inputs.hid.period                | How often, in seconds, to generate readings to AGD (defaults to 0.1). |



### Input processing: AGD

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| inputs.agd.source                | Input sensor source name: one of `arduino`, `audio` or `hid`.   |
| inputs.agd.buffer_size           | Input processor buffer size.                                    |
| inputs.agd.thresholds            | Input processor thresholds: adjusts "input sensor" responsiveness. |



### Input: Network

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| inputs.network.port              | TCP port where raw network connections will be accepted in.     |



### Input: Web

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| inputs.web.interface             | IP interface listening for HTTP connections.                    |
| inputs.web.port                  | TCP port listening HTTP connections.                            |



### Video files

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| levels.*.folder                  | Relative path to directory containing that level's video files. |
| levels.*.fadein                  | Fade in time, in seconds, for this level's video files.         |
| levels.*.fadeout                 | Fade out time, in seconds, for this level's video files.        |




About the "wind sensor"
-----------------------
The "wind sensor" used in the project is built out of an Arduino and some electronics amplifying and filtering the signals obtained from two "bend/flex sensors".

If anyone wants to have a go at it, the general idea, from this project's perspective is that the "wind sensor" input, configurable via `inputs.arduino.*` in the settings:

* Is available as a serial device.
* Sends ~10 readings per second.
* Each reading is three bytes:
  * The first byte should be 0x20.
  * The second and third bytes should be a 16 bit little endian integer, between 0 and 1023, where bigger means "more wind".

> Note: We've also successfully built a "wind sensor" variation with a [microbit](https://microbit-micropython.readthedocs.io/) and a single "bend sensor" for a Python only solution.




About the "audio sensor"
-----------------------
The "audio sensor" leverages the `arecord` ALSA utility's capability of monitoring an audio input without actually recording any audio.

Under the hood, an `arecord` instance is spawned with a command line like:
```
$ arecord --device==<device> --channels=<channels> --duration=0 --format <format> --rate=<rate> --buffer-time=<buffer_time> -vvv /dev/null
```

Each of the above `<value>` is sourced from the `settings.json` file under `inputs.audio.*`. Additionally, the actual `arecord` process is spawned under `nice` such that the audio capturing process does not interfere with the interactive responsiveness.

To test and adjust your "audio sensor":

* Run `arecord -L` to obtain a list of active ALSA devices.
* Run an `arecord` command line like the one above and observe the terminal based output: it should continuously print lines representing the input signal level.
* Try blowing, speaking, singing or shouting at the microphone and observe the level changes.
* Use the `alsamixer` utility to adjust the input gain, as needed, being careful enough to select the correct "sound card" and "capturing" view.

Once a usable configuration is found, with a solid enough signal, edit the `settings.json` file to include its settings.



About USB HID devices
---------------------
To identify available devices and supported event names, activate the virtual environment as described in the *Running* section and execute:

```
$ python -m evdev.evtest -c
```

It should display a list of input devices as in the example below, where a USB game pad and mouse are plugged in:

```
ID  Device               Name                                Phys
----------------------------------------------------------------------------------------
0   /dev/input/event0    Logitech Logitech RumblePad 2 USB   usb-3f980000.usb-1.2/input0
1   /dev/input/event1    Logitech USB-PS/2 Optical Mouse     usb-3f980000.usb-1.3/input0

Select devices [0-1]:
```

Then, at the `Select devices` prompt, enter the device ID to be used to obtain a list of capabilities and event code names. For example, selecting the mouse gives us:

```
Device name: Logitech USB-PS/2 Optical Mouse
Device info: bus: 0003, vendor 046d, product c03d, version 0110
Repeat settings: repeat 0, delay 0

Active keys: 

Device capabilities:
  Type EV_MSC 4:
    Code MSC_SCAN 4

  Type EV_REL 2:
    Code REL_X 0
    Code REL_Y 1
    Code REL_WHEEL 8

  Type EV_SYN 0:
    Code SYN_REPORT 0
    Code SYN_CONFIG 1
    Code SYN_MT_REPORT 2
    Code ?    4

  Type EV_KEY 1:
    Code BTN_LEFT, BTN_MOUSE 272
    Code BTN_RIGHT 273
    Code BTN_MIDDLE 274
```

Observe the lines under `EV_REL` containing `REL_X`, `REL_Y`: two good candidates to be used in `inputs.hid.reading_event_code`, tracking, respectively, the relative horizontal or vertical mouse movement.


If instead the game pad was selected at the `Select devices` prompt, one could obtain:

```
Device name: Logitech Logitech RumblePad 2 USB
Device info: bus: 0003, vendor 046d, product c218, version 0110
Repeat settings: repeat 0, delay 0

Active keys: 

Device capabilities:
  Type EV_FF 21:
    Code FF_EFFECT_MIN, FF_RUMBLE 80
    Code FF_PERIODIC 81
    Code FF_SQUARE, FF_WAVEFORM_MIN 88
    Code FF_TRIANGLE 89
    Code FF_SINE 90
    Code FF_GAIN, FF_MAX_EFFECTS 96

  Type EV_KEY 1:
    Code BTN_JOYSTICK, BTN_TRIGGER 288
    Code BTN_THUMB 289
    Code BTN_THUMB2 290
    Code BTN_TOP 291
    Code BTN_TOP2 292
    Code BTN_PINKIE 293
    Code BTN_BASE 294
    Code BTN_BASE2 295
    Code BTN_BASE3 296
    Code BTN_BASE4 297
    Code BTN_BASE5 298
    Code BTN_BASE6 299

  Type EV_SYN 0:
    Code SYN_REPORT 0
    Code SYN_CONFIG 1
    Code SYN_DROPPED 3
    Code ?    4
    Code ?    21

  Type EV_ABS 3:
    Code ABS_X 0:
      val 145, min 0, max 255, fuzz 0, flat 15, res 0
    Code ABS_Y 1:
      val 128, min 0, max 255, fuzz 0, flat 15, res 0
    Code ABS_Z 2:
      val 128, min 0, max 255, fuzz 0, flat 15, res 0
    Code ABS_RZ 5:
      val 128, min 0, max 255, fuzz 0, flat 15, res 0
    Code ABS_HAT0X 16:
      val 0, min -1, max 1, fuzz 0, flat 0, res 0
    Code ABS_HAT0Y 17:
      val 0, min -1, max 1, fuzz 0, flat 0, res 0

  Type EV_MSC 4:
    Code MSC_SCAN 4
```

In this case, under `EV_ABS`, entries like `ABS_X`, `ABS_Y`, `ABS_Z` and `ABS_RZ` are found, corresponding to each of the two axes in the two analog sticks in the game pad: good candidates to be used in `inputs.hid.reading_event_code`.





Development Notes
-----------------

### Code Overview

**Candle 2017** is a [Twisted](http://twistedmatrix.com/) application, with mostly asynchronous code, distributed across the following top-level components:

| module or package | Description |
|-------------------|-------------|
| `candle2017.py`   | Main entry point: loads the settings file, sets up the logging system, creates and starts an *input manager* and a *player manager*; ensures both are stopped on exit. |
| `common`          | Process spawning and tracking code used by `inputs` and `player`. |
| `inputs`          | Input related code: details below.                                |
| `log`             | Log setup and management code.                                    |
| `player`          | Video playing code: details below.                                |


Both `inputs` and `player` export a single name, `InputManager` and `PlayerManager` respectively, that implement a common interface: 

```
def __init__(self, reactor, wiring, settings):
    """
    Initializer:
    - `reactor` is the Twisted reactor.
    - `wiring` is a Python Wires instance, used to fire/handle event-like calls.
    - `settings` is a dict built out of the `settings.json` file.
    """

def start(self):
    """
    Returns a Twisted Deferred that fires on success or failure.
    """

def stop(self):
    """
    Returns a Twisted Deferred that fires on success or failure.
    """
```

A few notes on this:

* *one note*.
* *one more note*.




### The `player` package

Exports the `PlayerManager` class which handles all video playing:

* Spawns and tracks a private DBus instance process: see `dbus_manager.py`.
* Spawns one OMXPlayer process per level:
  * The level 0 player is spawned such that it plays in a loop.
  * The remaining level players are spawned and paused, ready to fade in and play at any time.
  * Each OMXPlayer for level N is set to play on visual layer above players for levels <N, such that visual fade ins/outs work effectively.
* OMXPlayer processes are tracked and controlled via the private DBus instance.
* Handles `wiring.change_play_level` calls in response to input triggered play level changes.

Additional notes:

* When changing play levels in response to input triggering, it just needs to "unpause" the respective level's OMXPlayer.
* Once a given level's OMXPlayer fades out and its process terminates, `PlayerManager` pre-emptively spawns another one, pausing it, to ensure the fastest possible response to future `wiring.change_play_level` calls.


The `OMXPlayer` class in `player.py` encapsulates the full interface to spawning, tracking and controlling and cleaning up individual OMXPlayer processes, including play/pause controls and automatic fade in/out on start/stop; like for most of the code, refer to the included comments and docstrings for the nitty gritty details.



### The `inputs` package

*write me*



Lint with:
```
$ pylint candle2017 common/ inputs/ player/ log/
```


Authors
-------
* [Nuno Godinho](https://github.com/nununo)
* [Tiago Montes](https://github.com/tmontes)


