#!/usr/bin/env bash
set -e
/usr/bin/mastersalt-call --retcode-passthrough --local -linfo mc_test.run_travis_tests
/usr/bin/salt-call --retcode-passthrough --local -linfo mc_test.run_travis_tests
# vim:set et sts=4 ts=4 tw=80:
