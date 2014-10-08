#!/usr/bin/env bash
cd "$(dirname $0)"
args=""
if [ "x$(mpt-status 2>/dev/null |grep ATA|wc -l)" != "x0" ];then
	args="-p mpt"
fi
./check_raid.pl $args $@
