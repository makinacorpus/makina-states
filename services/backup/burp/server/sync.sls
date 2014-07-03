{% set data = salt['mc_burp.settings']() %}
include:
  - makina-states.services.backup.burp.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
install-burp-configuration-sync:
  file.managed:
    - name: /etc/burp/clients/sync.sh
    - mode: 0755
    - user: root
    - group: root
    - contents: |
                {{'#'}}!/usr/bin/env bash
                gret="0"
                failed=""
                for i in \
                {% for client in data['clients'] %}    "{{client}}"\
                {%endfor%};do
                  # mark for backup on next contact if no backups found
                  if [ "x$(find "{{data.server_conf.directory}}/${i}" -mindepth 1 -maxdepth 1 -type d|wc -l|sed "s/ //g")" = "x0" ];then
                    if [ ! -e "{{data.server_conf.directory}}/${i}" ];then
                      mkdir -p "{{data.server_conf.directory}}/${i}"
                    fi
                    touch "{{data.server_conf.directory}}/${i}/backup"
                  fi
                  "/etc/burp/clients/${i}/sync.sh"
                  ret=$?
                  if [ "x${ret}" != "x0" ];then
                    gret=${ret}
                    failed="${failed} ${i}"
                  fi
                done
                if [ "x${gret}" != "x0" ];then
                  for i in ${failed};do
                    echo "Missed ${i}" 1>&2
                  done
                  exit $gret
                fi
                exit 0
  cmd.run:
    - name: /etc/burp/clients/sync.sh
    - use_vt: true
    - watch:
      - mc_proxy: burp-post-gen-sync
    - watch_in:
      - mc_proxy: burp-post-sync
{%endif %}
