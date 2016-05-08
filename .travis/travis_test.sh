#!/usr/bin/env bash
set -e
cd /srv/makina-states
bin/salt-call --retcode-passthrough --local -linfo test.ping
# vim:set et sts=4 ts=4 tw=80:
