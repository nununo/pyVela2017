Candle 2017 Code Overview
=========================

Preamble
--------

Please refer to the top-level [README](README.md) for general project information and references to other documents.

All code is internally documented with both docstrings and comments, while efforts have been made to use consistent and meaningful names all around.

Given that most of **Candle 2017** is about input, output and, generally, system level interactions (spawning processes, sending messages, handling external data and events, etc.) no automated tests are put in place; testing such interactions *is difficult* and error-prone, to say the last; suggestions will be welcomed, however.



High-level Overview
-------------------

**Candle 2017** is a [Twisted](http://twistedmatrix.com/) application, with mostly asynchronous code, distributed across the following top-level components:

| module or package | Description |
|-------------------|-------------|
| `candle2017.py`   | Main entry point: loads the settings file, sets up the logging system, creates and starts an *input manager* and a *player manager*; ensures both are stopped on exit. |
| `log`             | Log setup and management code.                                    |
| `common`          | Process spawning and tracking code used by `inputs` and `player`. |
| `inputs`          | Input related code: details below.                                |
| `player`          | Video playing code: details below.                                |


Both the `inputs` and `player` packages export a single name each: `InputManager` and `PlayerManager`, respectively, that implement a common interface: 

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

Notes:

* Making things run is just:
  * Instantiating one `InputManager` and one `PlayerManager`.
  * Calling `start` on each.

* `wiring` is a [Python Wires](https://pypi.python.org/pypi/wires/) instance:
  * Used as a callable-based event/notification system.
  * `PlayerManager` handles `wiring.change_play_level` calls.
  * `InputManager` triggers `wiring.change_play_level` calls.
  * Also used for cross-input communication and to push logs to web clients.



The `player` package
--------------------

Exports the `PlayerManager` class which handles all video playing:

* Spawns and tracks a private DBus instance process: see `dbus_manager.py`.
* Spawns one OMXPlayer process per level, attached to the private DBus instance:
  * The level 0 player is spawned such that it plays in a loop.
  * The remaining players are spawned and paused, ready to fade in and play at any time.
  * Each level N player displays on a visual layer above players for levels <N, such that fade ins/outs work.
* Player processes are tracked and controlled via the private DBus instance.
* Playing different level videos in response to input triggers is done by handling calls to `wiring.change_play_level`.


OMXPlayer life-cycle:

* `PlayerManager` always keeps a spawned player process per level.
* When changing play levels in response to input triggering, it "unpauses" the respective level's OMXPlayer.
* Once a given level's player fades out and its process terminates, a new one is pre-emptively spawned and paused, to ensure the fastest possible response to future play level changes.


The `OMXPlayer` class in `player.py` encapsulates the full interface to spawning, tracking, controlling and cleaning up individual OMXPlayer processes, including play/pause controls and automatic fade in/out on start/stop; like for most of the code, refer to the included docstrings and comments for the nitty-gritty details.



The `inputs` package
--------------------

Exports the `InputManager` class which:

* Instantiates and starts configured input objects on `start`.
* Stops previously started input objects on `stop`.


Input objects are instances of `InputBase` with a start/stop interface not different from the `InputManager`'s; all instances are created with the following initialization arguments:

* `reactor`, the Twisted reactor passed to `InputManager`.
* `wiring`, the Python Wires instance passed to `InputManager`.
* Other keyword arguments sourced from the `settings` dict passed to `InputManager`.



The `inputs.arduino` "wind sensor" package
------------------------------------------

At start time:

* Opens the configured serial port.
* Attaches an instance of `ArduinoProtocol` to it.
* Sets `ArduinoProtocol` to call `wiring.arduino` with each reading.



The `inputs.audio` "audio sensor" package
-----------------------------------------

At start time:

* Spawns an `arecord` process with command line arguments per the configuration.
* Tracks the process:
  * If it ever stops re-spawns it, unless configured not to.
  * Processes its STDERR, parsing each line matching an "audio input level reading".
  * Calls `wiring.audio` with each reading.



The `inputs.hid` package
------------------------

This input operates at two levels:
* Tracks the configured USB HID events asynchronously.
* Generates a constant stream of readings based on those events.

At instantiation time:

* Creates an `InputDeviceReader` that operates asynchronously, processing all of the configured device's events.
* Each event matching the configuration will have its value stored on the input object via `_store_reading`.


At start time:

* Starts the `InputDeviceReader` which will call `_store_reading` asynchronously.
* Starts the the periodic sending of readings via `_send_reading_later`.

Much like the other inputs, readings are "sent out" by calling `wiring.hid`.



The `inputs.agd` package
------------------------

At instantiation time:

* Sets itself to handle `wiring.<source>` calls to process "sensor readings".
* `wiring.<source>` depends on the AGD input configuration from the settings file, where \<source> will be one of `arduino`, `audio` or `hid`, matching the wiring calls on respective inputs.


For each reading:

* Updates its aggregated derivative calculation (details in the code docstrings and comments).
* Depending on the calculated value and level thresholds, calls `wiring.change_play_level` to trigger video playing level changes.
* Always calls `wiring.agd_output` with the current raw reading and calculated aggregated derivative (these will be used by the web interface).


About the thresholds:

* Initially sourced from the settings file.
* Can be monitored and changed at run-time:
  * Handles `wiring.request_agd_thresholds` calls, responded to with `wiring.notify_agd_threshold` calls containing the current threshold levels.
  * Handles `wiring.set_agd_threshold` calls that change a given level's threshold.



The `inputs.web` package
------------------------

This input is a hybrid thing:

* Acts as an input, able to trigger video playing level changes.
* Acts as a monitoring tool, displaying input readings in a chart, AGD thresholds and logs.
* Supports changing AGD thresholds and setting log levels at run-time.

It is also hybrid in the sense that part of it is written in Python while the web client side code is written in Javascript.


Overview:

* Web clients request the root resource.
* `index.html` is served including the HTML layout with embedded CSS, containing links to:
  * A bundled version of the [charts.js](https://www.chartjs.org) Javascript compressed and minified code.
  * A bundled version of the  [chartjs-plugin-annotation.js](https://github.com/chartjs/chartjs-plugin-annotation) Javascript compressed and minified code.
  * `index.js`, the Javascript web client code.
* Once loaded, the client initiates a WebSocket connection to the server.


The WebSocket connection is used for bidirectional communication:

* Server to client pushes:
  * Log messages, depending on the log level settings.
  * Input sensor readings and AGD values, to be displayed in the chart.
  * AGD threshold levels, to be displayed in the chart.

* Client to server change requests:
  * Video playing level.
  * AGD thresholds.
  * Log levels.


WebSocket messages are single JSON objects:

* Server to client pushes:
  * The `type` property indicates the type of push.
  * Other properties hold the pushed data.

* Client to server requests:
  * The `action` property indicates the nature of the request.
  * Other properties hold request data.


Server side WebSocket connection life-cycle:

* At WebSocket connection establishment time, the server side protocol instance:
  * Adds itself as a Twisted logging observer, to push log messages to the client.
  * Sets itself to handle `wiring.agd_output` calls, to push raw readings and AGD values to the client.
  * Sets itself to handle `wiring.notify_agd_threshold` calls, to push AGD threshold values to the client.
  * Calls `wiring.request_agd_thresholds` asking AGD to notify about the current thresholds.

* For each WebSocket received message:
  * Video playing level change requests call `wiring.change_play_level`.
  * AGD threshold change requests call `wiring.set_agd_threshold`.
  * Log level change requests call `wiring.set_log_level`.

* At WebSocket disconnection time, the server side protocol instance:
  * Removes itself as a Twisted logging observer.
  * Stops handling `wiring.agd_output` calls.
  * Stops handling `wiring.notify_agd_threshold` calls.


For more details refer to the included docstrings and comments in either Python or Javascript code.




The `inputs.network` package
----------------------------

*write me*



Wrapping up
-----------

*write me*

Lint with:
```
$ pylint candle2017 common/ inputs/ player/ log/
```



More
----

Please refer to the top-level [README](README.md) for general project information and references to other documents.


