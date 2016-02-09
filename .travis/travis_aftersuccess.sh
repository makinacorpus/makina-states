#!/usr/bin/env bash
set -e
cd "$(dirname ${0})/.."
. bin/activate
coveralls
# VIM:set et sts=4 ts=4 tw=80:
