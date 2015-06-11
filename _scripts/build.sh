#!/usr/bin/env bash
set -x
cd $(dirname $0)
cwd=$(pwd)
cd $cwd/..
docker run --privileged -ti --rm \
        -v /usr/bin/docker:/usr/bin/docker:ro \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /var/run/docker:/var/run/docker \
        -v /var/lib/docker:/var/lib/docker \
        -v /sys/fs:/sys/fs:ro\
        -v $PWD:/data \
        -v $PWD/_scripts/docker_build.sh:/bootstrap_scripts/docker_build.sh\
        makinacorpus/makina-states-vivid-0
# vim:set et sts=4 ts=4 tw=80:
