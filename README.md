Candle 2017
===========

About
-----

**Candle 2017** is a re-implementation of an [interactive art project by Nuno Godinho](https://projects.nunogodinho.com/candle), whereby a beautifully framed high quality display shows a candle burning video, against a pitch black background. Blowing into the display triggers natural candle reactions: the flame flickers more or less depending on the blowing strength and can even be fully blown out with a strong enough blow - when so, the base candle burning video is restarted and smoothly faded in after a few seconds.

Originally written in C++ using OpenFrameworks, Nuno never got it to run with acceptable performance on the desired target platform, a Raspberry Pi; it required being driven by a much more powerful and expensive system, like a Mac Mini.

This project is a Python implementation that succeeds in delivering the required performance on a Raspberry Pi.

> Heads up: there are no silver bullets here! It's not like Python on a Raspberry Pi has suddenly more performance than well written C++ code on a Mac Mini. It just takes a completely different approach, better leveraging the available resources on the smaller system.



Documentation
-------------

Refer to [Running Candle 2017](README-running.md) to learn everything about the requirements, installation, configuring, running, and using **Candle 2017**.

For a high level overview of the code see [Candle 2017 Code Overview](README-develop.md), keeping in mind that going through [Running Candle 2017](README-running.md) first is recommended.



Thanks
------

This project wouldn't be possible without using several open source software packages. Here's a thank you note to the projects **Candle 2017** directly depends on; in particular to their authors, maintainers, contributors and sponsors:

* [Python](https://www.python.org/), the language and interpreter.
* [Twisted](https://twistedmatrix.com/), an event-driven networking engine.
* [txdbus](https://pypi.python.org/pypi/txdbus), a Twisted based interface to DBus.
* [autobahn](https://crossbar.io/autobahn/), for its Twisted based WebSocket implementation.
* [evdev](https://pypi.python.org/pypi/evdev), for its bindings to the Linux input handling subsystem.
* [omxplayer](https://github.com/popcornmix/omxplayer), a flexible and high-performance Raspberry Pi command line video player.
* [ALSA](https://www.alsa-project.org/main/index.php/Main_Page), the Advanced Linux Sound Architecture project.
* [charts.js](https://www.chartjs.org), a simple yet flexible JavaScript charting library.
* [chartjs-plugin-annotation.js](https://github.com/chartjs/chartjs-plugin-annotation), a charts.js plugin that draws lines and boxes on the chart area.



Authors
-------

* [Nuno Godinho](https://github.com/nununo)
* [Tiago Montes](https://github.com/tmontes)


