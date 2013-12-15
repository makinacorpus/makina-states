#!/usr/bin/env bash
prefix="$1"
for i in _states _grains _modules _renderers _returners;do
     if [[ ! -d  "$prefix/$i" ]];then mkdir "$prefix/$i";fi;
     for f in $(find $prefix/makina-states/$i -name "*py" -type f);do
         ln -vsf "$f" "$prefix/$i";
     done;
done;
# vim:set et sts=4 ts=4 tw=80:
