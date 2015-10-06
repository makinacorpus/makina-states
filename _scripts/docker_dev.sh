#!/usr/bin/env bash
# this can be used to grab a git folder in docker images when lot of things have been trimmed out
set -xe
apt-get update
apt-get install -y vim ncdu
if [ ! -e /srv/salt/makina-states/.git ];then
    git clone https://github.com/makinacorpus/makina-states.git /srv/salt/makina-states/git
    mv /srv/salt/makina-states/git/.git /srv/salt/makina-states/
fi
if [ ! -e /srv/mastersalt/makina-states/.git ];then
    cp -rf /srv/salt/makina-states/.git /srv/mastersalt/makina-states/.git
fi
rm -rf /srv/salt/makina-states/git
if [ ! -e /salt-venv/salt/src/salt/.git ];then
    git clone http://github.com/makinacorpus/salt.git /salt-venv/salt/src/salt/git
    mv /salt-venv/salt/src/salt/git/.git /salt-venv/salt/src/salt/.git
fi
if [ ! -e /salt-venv/mastersalt/src/salt/.git ];then
    cp -rf /salt-venv/salt/src/salt/.git /salt-venv/mastersalt/src/salt/.git
fi
rm -rf /salt-venv/salt/src/salt/git
# vim:set et sts=4 ts=4 tw=80:
