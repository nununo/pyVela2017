Candle 2017
===========

About
-----

**Candle 2017** is a re-implementation of an interactive art project by Nuno Godinho (https://projects.nunogodinho.com/candle/).

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
* Candle burning videos (you'll need to create these yourself).


Full Requirements
-----------------
For full interactivity, some kind of "input sensor" is needed.

As of this writing, two distinct "input sensor" types are supported:

* The original "blow sensor", as used in the art project itself, comprised of multiple "bend sensors" wired to an arduino that, in turn, continuously delivers "bend readings": these will be bigger as the "wind blowing towards the screen" strength increases, forcing the "bend sensors" to move.

* An alternative "audio sensor", much simpler and accessible, based on sound input; this requires prior setup of the ALSA subsystem such that, for example, a USB microphone or webcam audio can be used.

Either "input sensor" can be tuned in a way such that varying inputs (more/less wind or louder/softer sound) trigger natural candle reactions, including blowing out the candle.



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
* It should have four sub-directories, each containing one or more candle burning videos:
  * `0`: played in a loop when no interaction is detected.
  * `1`: triggered by *light blowing*.
  * `2`: triggered by *medium blowing*.
  * `3`: triggered by *strong blowing* (in the original project, the burning flame is blown out).

Copy `settings-sample.json` to `settings.json` and adapt it according to your environment. See the Configuration section below for details. 


 
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

