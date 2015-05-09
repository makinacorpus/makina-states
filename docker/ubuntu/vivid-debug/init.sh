#!/usr/bin/env bash
exec strace -f -D -o /strace.log /systemd.sh
# vim:set et sts=4 ts=4 tw=80:
