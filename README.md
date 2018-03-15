Candle 2017
===========

About
-----

**Candle 2017** is a re-implementation of an [interactive art project by Nuno Godinho](https://projects.nunogodinho.com/candle), whereby a beautifully framed high quality display shows a candle burning video, against a pitch black background. Blowing into the display triggers natural candle reactions: the flame flickers more or less depending on the blowing strength and can even be fully blown out with a strong enough blow - when so, the base candle burning video is restarted and smoothly faded in after a few seconds.

Originally written in C++ using OpenFrameworks, Nuno never got it to run with acceptable performance on the desired target platform, a Raspberry Pi; it required being driven by a much more powerful and expensive system, like a Mac Mini.

This project is a Python implementation that succeeds in delivering the required performance on a Raspberry Pi.

> Heads up: there are no silver bullets here! It's not like Python on a Raspberry Pi has suddenly more performance than well written C++ code on a Mac Mini. It just takes a completely different approach, better leveraging the available resources on the smaller system.



Linked documentation
--------------------

Refer to [Running Candle 2017](README-running.md) to learn everything about the requirements, installation and set up, running, and using **Candle 2017**.

For a high level overview of the code see [Candle 2017 Code Overview](README-develop.md).



Thanks
------

*write me*



Authors
-------

* [Nuno Godinho](https://github.com/nununo)
* [Tiago Montes](https://github.com/tmontes)


