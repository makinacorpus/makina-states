#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from bottledaemon import daemon_run
from bottle import route, request
import time
import os


@route("/hello")
def hello():
    return "hello :: {0}\n".format(
        request.environ['HTTP_HOST'])


@route("/api")
def api():
    return "api called\n"


@route("/ping")
@route("/ping/<sleeptime:int>")
def ping(sleeptime=0):
    time.sleep(sleeptime)
    return "pong\n"


if __name__ == "__main__":
    try:
        port = os.environ['BOTTLE_PORT']
    except KeyError:
        port = 4343
    daemon_run(host="0.0.0.0", port=port)
