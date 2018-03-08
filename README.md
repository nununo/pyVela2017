Candle 2017
===========

About
-----

**Candle 2017** is a re-implementation of an interactive art project by Nuno Godinho <sup id="a1">[1](#f1)</sup>, whereby a beautifully framed high quality display shows a candle burning video, against a pitch black background. Blowing into the display triggers natural candle reactions: the flame flickers more or less depending on the blowing strength and can even be fully blown out with a strong enough blow -- when so, the base candle burning video is restarted and smoothly faded in after a few seconds.

<sup id="f1">[1]</sup> https://projects.nunogodinho.com/candle (back)[#a1]

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
* Four sets of candle burning video files [2]:
  * Level 0: stable candle burning with no interference, played in a loop.
  * Level 1: candle flame flickering, responding to light blowing.
  * Level 2: candle flame flickering, responding to medium blowing.
  * Level 3: candle flame blowing out, responding to strong blowing.
  * Any of these sets can contain multiple files: **Candle 2017** will select one at random from a given level, when the respective interaction is triggered.

[2] You will need to create these yourself.


With these in place you will be able to explore **Candle 2017** and trigger candle reactions artificially, either via a web based monitoring and controlling interface or via a simpler network based control interface (more on this, below).



Full Requirements
-----------------
For full, natural interactivity, an input sensor is needed.

As of this writing, two distinct input sensor types are supported:

* The original "wind sensor", as used in the art project itself, comprised of multiple "bend/flex sensors" [3] integrated within the display frame, wired to an arduino that, in turn, continuously delivers "bend readings": these will be bigger as the "wind blowing towards the screen" strength increases, forcing the "bend/flex sensors" to move.

* An alternative "audio sensor", much simpler and accessible, based on sound input; this requires prior setup of the ALSA subsystem such that, for example, a USB microphone or webcam audio can be used: naturally, this input sensor reacts to directed blows and also to environment sound pressure/level.

Either input sensor is fed into an input processor, called AGD, that can be tuned in a way such that varying inputs (more/less wind or louder/softer sound) trigger the natural candle reactions by playing videos in different levels.


[3] See https://en.wikipedia.org/wiki/Flex_sensor.



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
* It should have four sub-directories, named `0`, `1`, `2` and  `3`, each containing one or more candle burning videos of the given level, as described in the requirements.

Copy `settings-sample.json` to `settings.json` and adapt it according to your environment, paying particular attention to the input configuration. For more details, refer to the *Configuration* section, below.


 
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
* The Python process running `candle2017.py` should have the following children:
  * One `dbus-daemon` process.
  * Four `omxplayer.bin` processes.
  * One `arecord` process, if the "audio" input is included in the configuration.
* One of the videos in the `videos/0` directory should be playing, in a loop.
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
As an interactive art project, using it is about interacting with it. There are currently four ways to interact:

**"Wind sensor" interaction**

* Requires "wind sensor" to be present.
* Requires `inputs.agd.source` to be set to `"arduino"`, which is the default.
* May need adjustments to `inputs.agd.buffer_size` and `inputs.agd.thresholds` in the configuration.
* Blow on the sensor and watch the candle react.
* It is recommended to remove the "audio" input from the `settings.json` file.


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



**Web based network monitoring and control**

* Point a web browser to http://\<raspberry-pi-IP\>:\<port\>/, where <port> is defined by `inputs.web.port` in the configuration (defaults to 8080).
* Monitor the real-time "wind sensor" reading in the top left chart.
* Observe the "agd" thresholds and click them to adjust.
* Track log messages on the top right pane.
* Use the buttons on the bottom to trigger video level changes.

> Important: multiple browser connections are accepted simultaneously; no effort to authenticate or limit the amount of connections is made.


**ALSA Audio based input**

* Requires configuration of an ALSA audio input device.
* Adjust `inputs.audio.*` settings.
* Set `inputs.agd.source` to `"audio"`.
* May need adjustments to `inputs.agd.buffer_size` and `inputs.agd.thresholds` in the configuration.
* Produce different sound levels (including blowing into the microphone) and watch the candle react.
* It is recommended to remove the "arduino" input from the `settings.json` file.


Configuration
-------------
When running, the configuration is sourced from the file `settings.json`. As its name implies, it is a JSON formatted file containing all the configurable settings.

Most settings are, hopefully, self-explanatory. Here's a quick rundown:

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| environment.dbus_daemon_bin      | Absolute path to the `dbus-daemon` executable.
| environment.omxplayer_bin        | Absolute path to the `omxplayer.bin` executable.                |
| environment.ld_library_path      | Absolute path to the OMXPlayer required shared libraries.       |
| loglevel                         | Default log level, one of `debug`, `info`, `warn` or `error`.   |
| loglevel.*                       | Per component log level.                                        |
| inputs.arduino.device_file       | Absolute path to the serial device file of the "wind sensor".   |
| inputs.arduino.baud_rate         | Baud rate of the "wind sensor" communication.                   |
| inputs.audio.nice_bin            | Absolute path to the `nice` executable.                         |
| inputs.audio.arecord_bin         | Absolute path to the `arecord` executable.                      |
| inputs.audio.device              | ALSA device as obtained from the output `arecord -L`.           |
| inputs.audio.channels            | Number of channels to "listen on".                              |
| inputs.audio.format              | Audio capture format, to be used in `arecord`'s `--format` option. |
| inputs.audio.rate                | Audio capture rate, to be used in `arecord`'s `--rate` option. |
| inputs.audio.buffer_time         | Audio capture buffer size, to be used in `arecord`'s `--buffer-size` option. |
| inputs.audio.respawn_delay       | Delay, in seconds, to wait for `arecord` process re-spawn (no re-spawns will be attempted if negative). |
| inputs.agd.source                | Input sensor source name: currently only `arduino` is supported. |
| inputs.agd.buffer_size           | Input sensor buffer size.
| inputs.agd.thresholds            | Input sensor thresholds: adjusts "input sensor" responsiveness. |
| inputs.network.port              | TCP port where raw network connections will be accepted in.     |
| inputs.web.interface             | IP interface listening for HTTP connections.                    |
| inputs.web.port                  | TCP port listening HTTP connections.                            |
| levels.*.folder                  | Relative path to directory containing that level's video files. |
| levels.*.fadein                  | Fade in time, in seconds, for this level's video files.          |
| levels.*.fadeout                 | Fade out time, in seconds, for this level's video files.        |


About the "wind sensor"
-----------------------
The "wind sensor" used in the project is built out of an Arduino and some electronics amplifying and filtering the signals obtained from two "bend sensors".

If anyone wants to have a go at it, the general idea, from this project's perspective is that the "wind sensor" input, configurable via `inputs.arduino.*` in the settings:

* Is available as a serial device.
* Sends ~10 readings per second.
* Each reading is three bytes:
  * The first byte should be 0x20.
  * The second and third bytes should be a 16 bit little endian integer, between 0 and 1023, where bigger means "more wind".

PS: We've also prototyped a "wind sensor" with a microbit (https://microbit-micropython.readthedocs.io/) and a single "bend sensor" for a Python only solution.


Development Notes
-----------------

Lint with:
```
$ pylint candle2017 common/ inputs/ player/ log/
```


Authors
-------
* Nuno Godinho (@nununo)
* Tiago Montes (@tmontes)

