#!/usr/bin/env bash
docker rm -f $(docker ps -a|grep  Exited|grep "sh -c 'echo" |awk '{print $1}')
docker rm -f $(docker ps -a|grep  Exited|grep "sh -c '#(nop)" |awk '{print $1}')
docker rm -f $(docker ps -a|grep  Exited|grep '"bash"' |awk '{print $1}')
docker rmi $(docker images --filter dangling=true -q)
# vim:set et sts=4 ts=4 tw=80:
