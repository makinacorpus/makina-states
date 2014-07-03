{% set data = salt['mc_burp.settings']() %}
include:
  - makina-states.services.backup.burp.hooks
  - makina-states.services.backup.burp.server.sync
  - makina-states.services.backup.burp.server.cleanup
{% if salt['mc_controllers.mastersalt_mode']() %}
{% for client, cdata in data['clients'].items() %}
{{client}}-install-burp-configuration:
  file.managed:
    - name: /etc/burp/clients/{{client}}/sync.sh
    - mode: 0755
    - user: root
    - group: root
    - watch_in:
      - mc_proxy: burp-post-restart-hook
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

burp-svc:
  service.running:
    - name:  burp-server
    - reload: True
    - watch:
      - mc_proxy: burp-pre-restart-hook
    - watch_in:
      - mc_proxy: burp-post-restart-hook
{%endif %}
