#!/usr/bin/env bash
cd $(dirname $0)/..
cwd=$PWD
$cwd/bin/salt-call -lall state.sls makina-states.test
