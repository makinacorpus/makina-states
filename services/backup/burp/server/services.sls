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
{% set scdata = salt['mc_utils.json_dump'](cdata) %}

{{client}}-install-burp-configuration:
  file.managed:
    - name: /etc/burp/clients/{{client}}/sync.sh
    - mode: 0755
    - user: root
    - group: root
    - contents: |
            {{'#'}}!/usr/bin/env bash
            {% for dir in ['burp', 'default', 'init.d', 'cron.d'] -%}rsync -azv /etc/burp/clients/{{client}}/etc/{{dir}}/ {{client}}:/etc/{{dir}}/ &&\
            {% endfor -%}
            /bin/true
            {% if not cdata.activated -%}
            ssh {{client}} rm -f /etc/cron.d/burp
            {% endif %}
            {#
            ssh {{client}} update-rc.d -f burp-client remove &&
            ssh {{client}} /etc/init.d/burp-client stop
            {% else -%}
            ssh {{client}} update-rc.d -f burp-client defaults 99 &&\
            ssh {{client}} /etc/init.d/burp-client reload
            {% endif %}#}
  cmd.run:
    - name: /etc/burp/clients/{{client}}/sync.sh
    - watch:
      - service: burp-svc
      - file: {{client}}-install-burp-configuration
    - watch_in:
      - mc_proxy: burp-post-restart-hook
{% endfor %}

{# this is a cronjob which run burp and not an daemon
burp-client-svc:
  service.enabled:
    - name:
      - burp-client
    - reload: True
    - watch_in:
      - mc_proxy: burp-post-restart-hook
#}
{%endif %}
