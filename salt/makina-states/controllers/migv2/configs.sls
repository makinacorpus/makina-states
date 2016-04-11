{% set locs = salt['mc_locations.settings']() %}
merge_configs:
  file.directory:
    - name: {{data.msr}}/etc/makina-states
  cmd.run:
    - require:
      - file: merge_configs
    - name: |
            cd /etc
            cp -fv makina-states/nodetype {{data.msr}}/etc/makina-states
            find mastersalt/makina-states salt/makina-states makina-states\
              -type f|\
              egrep ".(nodetype|yaml|jinja|json|pack)"|\
              egrep -v "(cloud|services|controllers|localsettings|nodetypes).yaml"|\
              while read f;do
                if [ ! -h $f ]; then
                  cp -v $f {{data.msr}}/etc/makina-states
                  ln -sfv {{data.msr}}/etc/makina-states/$(basename ${f}) ${f}
                fi
              done
            find mastersalt/makina-states salt/makina-states makina-states|\
              -type f|\
              egrep ".(nodetype|yaml|jinja|json|pack)"|\
              egrep "(cloud|services|controllers|localsettings|nodetypes).yaml"|\
              while read f;do
                if [ ! -h $f ]; then
                  grep -i ": true" $f \
                    > {{data.msr}}/etc/makina-states/$(basename $f)
                  ln -sfv {{data.msr}}/etc/makina-states/$(basename ${f}) ${f}
                fi
              done
