#!/usr/bin/env bash
cd "$(dirname $0)"
CIRCUS_WATCHER={{name}} ./manager.sh $@
# vim:set et sts=4 ts=4 tw=80:
