#!/usr/bin/env bash
for i in 0 $(seq 3 20); do
    echo "ThreadsNumber: $i"
    time mastersalt-call --local -linfo mc_remote_pillar.replicate_masterless_pillars threads=$i
done
# vim:set et sts=4 ts=4 tw=80:
