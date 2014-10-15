#!/usr/bin/env bash
cd "$(dirname $0)"
args=""
plugins=""
if [ -e /proc/mdstat ];then
    if [ "x$(cat /proc/mdstat 2>/dev/null|grep -q "active rai";echo ${?})" = "x0" ];then
        plugins="${plugins},mdstat"
    fi
fi
if [ "x$(which mpt-status 2>/dev/null)" != "x" ];then
    if [ "x$(lspci|grep -q Fusion-MPT;echo ${?})" = "x0" ];then
        if [ "x$(mpt-status -p 2>/dev/null|grep -q "Found SCSI";echo ${?})" = "x0" ];then
            plugins="${plugins},mpt"
        fi
    fi
fi
if [ "x$(which megacli 2>/dev/null)" != "x" ];then
    megainfo="$(megacli -adpCount 2>/dev/null|grep Count|awk -F: '{print $2}'|sed "s/\.//g"|sed "s/ //g")"
    if [ "x$megainfo" != "x0" ];then
        plugins="${plugins},megacli"
    fi
fi
if [ "x$(which sas2ircu 2>/dev/null)" != "x" ];then
   if [ "x$(sas2ircu LIST 2>&1 1>/dev/null;echo $?)" = "x0" ];then
        plugins="${plugins},sas2ircu"
   fi
fi
if [ "x$(which hpacucli 2>/dev/null)" != "x" ];then
    if [ "x$(hpacucli ctrl all show 2>&1 1>/dev/null;echo $?)" = "x0" ];then
        plugins="${plugins},hpacucli"
    fi
fi
plugins="$(echo "${plugins}"|sed -re "s/^,//g")"
if [ "x${plugins}" != "x" ];then
    args="-p $plugins"
fi
./check_raid.pl $args $@
