include:
  - makina-states.services.backup.burp.hooks
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
{{client}}-install-configuration:
  cmd.run:
    - watch:
      - service: burp-svc
    - watch_in:
      - mc_proxy: burp-post-restart-hook
    - name: |
            {% for dir in ['burp', 'default', 'init.d', 'cron.d'] -%}
            rsync -azv /etc/burp/clients/{{client}}/etc/{{dir}}/ {{client}}:/etc/{{dir}}/ &&
            {%- endfor %}
            ssh {{client}} update-rc.d -f burp-client defaults 99 &&
            ssh {{client}} /etc/init.d/burp-client restart
#}
{% endfor %}
