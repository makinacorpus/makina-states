#!/usr/bin/env bash
# try to cleanup most of the dangling containers and images
docker ps -a|grep  Exited|grep "sh -c 'echo" |awk '{print $1}'|while read i;do
    docker rm -f $i
done
docker ps -a|grep  Exited|grep "sh -c '#(nop)" |awk '{print $1}'|while read i;do
    docker rm -f $i
done
docker ps -a|grep  Exited|grep '"bash"'\
    | egrep -v "mysql|postgresql|pgsql|redis|mongodb|storage|backup"\
    | awk '{print $1}'|while read i;do
    docker rm -f $i
done
docker images --filter dangling=true -q|while read i;do
    docker rmi $i
done
# vim:set et sts=4 ts=4 tw=80:
