include:
  - makina-states.services.backup.burp.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
{% set data = salt['mc_burp.settings']() %}
burp-svc:
  service.enabled:
    - name:  burp-server
    - reload: True
    - watch:
      - mc_proxy: burp-pre-restart-hook
    - watch_in:
      - mc_proxy: burp-post-restart-hook

{% for client, cdata in data['clients'].items() %}
{{client}}-install-burp-configuration:
  file.managed:
    - name: /etc/burp/clients/{{client}}/sync.sh
    - mode: 0755
    - user: root
    - group: root
    - watch_in:
      - file: install-burp-configuration-sync
    - contents: |
            {{'#'}}!/usr/bin/env bash
            {% for dir in ['burp', 'default', 'init.d', 'cron.d'] -%}rsync -azv -e '{{cdata['rsh_cmd']}}' /etc/burp/clients/{{client}}/etc/{{dir}}/ {{cdata['rsh_dst']}}:/etc/{{dir}}/ &&\
            {% endfor -%}
            /bin/true
            {% if not cdata.activated -%}
            {{cdata['ssh_cmd']}} rm -f /etc/cron.d/burp
            {% endif %}
            exit ${?}


{% endfor %}

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
    - watch:
      - service: burp-svc
      - file: install-burp-configuration-sync
    - watch_in:
      - mc_proxy: burp-post-restart-hook
{%endif %}
