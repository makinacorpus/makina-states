#!/usr/bin/env bash
set -e
cd /srv/mastersalt/makina-states
/usr/bin/mastersalt-call --retcode-passthrough --local -linfo mc_test.run_travis_tests
cd /srv/salt/makina-states
/usr/bin/salt-call --retcode-passthrough --local -linfo mc_test.run_travis_tests
# vim:set et sts=4 ts=4 tw=80:
