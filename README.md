Vela 2017
=========

About
-----

**Vela 2017** is a reimplementation of an interactive art project by Nuno Godinho (https://projects.nunogodinho.com/candle/).

Originally written in C++ using OpenFrameworks, Nuno never got it to run with acceptable performance on the desired target platform, a Raspberri Pi; it required being driven by a much more powerful and expensive system, like a Mac Mini.

This project is a Python reimplementation that succeeds in delivering the required performance on a Raspberri Pi.

> Heads up: there are no silver bullets here! It's not like Python on a Raspberry Pi is suddenly more performant than well written C++ code on a Mac Mini. It just takes a completely different approach, better leveraging the available resources on the smaller system.


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
For full *interactivity*, a serial input device attached to a some kind of "wind sensor" is needed, such that blowing into the video triggers natural candle reactions (more on this later).


Installation
------------

Install the required raspbian packages:
```
$ sudo apt-get update
$ sudo apt-get install python3 python3-virtualenv omxplayer dbus git
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
* It should have four subdirectories, each containing one or more candle burning videos:
  * `0`: played in a loop when no interaction is detected.
  * `1`: triggered by *light blowing*.
  * `2`: triggered by *medium blowing*.
  * `3`: triggered by *strong blowing* (in the original project, the burning flame is blown out).

Copy `settings-sample.json` to `settings.json` and adapt it according to your environment. See Configuration section below for details. 
 
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

(optionally, make `candle2017.py` executable with `chmod u+x candle2017.py` and run it with `./candle2017.py`)

Once running:
* Log messages will be output to `stderr`; see below to learn how to adjust logging details.
* Four `omxplayer.bin` processes should be running as child processes.
* One of the videos in the `videos/0` directory should be playing, in a loop.

Stopping:
* Hit CTRL-C on the shell that launched the program.
* Send a SIGTERM to the Python process running `candle2017.py`.


Using
-----
As an interactive art project, using it is about interacting with it. There are currently three ways to interact:

**"Wind sensor" interaction**

* Requires "wind sensor" to be present.
* May need adjustments to `inputs.arduino.thresholds` in the configuration.
* Blow on the sensor and watch the candle react.

**Raw TCP network control**

* Use telnet or netcat to establish a TCP connection towards the Raspberri Pi on the TCP port defined by `inputs.network.port` in the configuration (defaults to 10000).
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

* Point a web browser to http://\<raspberry-pi-IPv\>:8080/.
* Monitor the realtime "wind sensor" reading in the top left chart.
* Track log messages on the top right pane.
* Use the buttons on the bottom to trigger video level changes.

> Important: multiple browser connections are accepted simultaneously, however only the *most recent connection* will actually be usable; also, no authentication is in place.


Configuration
-------------
When running, the configuration is sourced from the file `settings.json`. As its name implies, it is a JSON formatted file containing all the configurable settings.

Most settings are, hopefully, self-explanatory. Here's a quick rundown:

| setting                          | description                                                     |
|----------------------------------|-----------------------------------------------------------------|
| environment.dbus_run_session_bin | Absolute path to the `dbus-run-session` executable.
| environment.omxplayer_bin        | Absolute path to the `omxplayer.bin` executable.                |
| environment.ld_library_path      | Absolute path to the OMXPlayer required shared libraries.       |
| loglevel                         | Default log level, one of `debug`, `info`, `warn` or `error`.   |
| loglevel.*                       | Per component log level.                                        |
| inputs.arduino.device_file       | Absolute path to the serial device file of the "wind sensor".   |
| inputs.arduino.baud_rate         | Baud rate of the "wind sensor" communication.                   |
| inputs.arduino.thresholds        | Array of three integers: adjust "wind sensor" responsiveness.   |
| inputs.network.port              | TCP port where raw network connections will be accepted in.     |
| levels.*.folder                  | Relative path to directory containing that level's video files. |
| levels.*.fadein                  | Fade in time, in secods, for this level's video files.          |
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
$ pylint candle2017 inputs/ player/ webserver/ log/
```


Authors
-------
* Nuno Godinho
* Tiago Montes
