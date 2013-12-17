#!/usr/bin/env bash
cd $(dirname $0)

# replace set dummy by do block
# sed -re "s/set\s+dummy\s*=\s*/do /g" -i $(grep -r "ummy" se* bootstrap setup* localsettings/ _macros/|awk -F: '{print $1}'|sort -u)

# replace {{aa}} by {{ aa }}
# sed -re "s/\{\{\s*([^} ]*)\}\}/{{ \1 }}/g" -i $(find bootstraps nodetypes/ _macros/ controllers/ localsettings/ services/ -type f) 

# replace {% set foo = {% azert by {% set foo = azert
# sed -re "s/(\{% set [^=]*)=\s*\{%\s*(.*)/\1 = \2/g"  $(cat locfiles) -i

# regenerate a list to grep / sed into
# find bootstraps controllers/ files/ localsettings/ _macros/ nodetypes/ services/ top.sls  -type f>locfiles

# sync the only needed in makina-states for mastersalt
# (quickier in virtualbox)
# for i in src/salt/ files/ _scripts/ bootstraps/ top.sls buildout.cfg _modules/ _states/ services/ localsettings/ controllers/ nodetypes/ _macros/;do rsync -vPa --exclude=*pyc --exclude=*pyo --exclude=.installed.cfg --exclude=.mr.developer.cfg --exclude=.bootlogs --exclude=.git /srv/salt/makina-states/$i /srv/mastersalt/makina-states/$i;done
