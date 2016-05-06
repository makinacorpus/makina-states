{% import "makina-states/_macros/h.jinja" as h with context %}
{% set data = salt['mc_haproxy.settings']() %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.services.proxy.haproxy.services

{% macro rmacro() %}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
{% endmacro %}
{{ h.deliver_config_files(
     data.get('configs', {}),
     mode='644',
     after_macro=rmacro, prefix='haproxy-')}}

makina-haproxy-cleanup-old:
  file.absent:
    - names:
      - "{{data.config_dir}}/frontends/"
      - "{{data.config_dir}}/backends/"
      - "{{data.config_dir}}/dispatchers/"
      - "{{data.config_dir}}/listeners/"
      - "{{data.config_dir}}/extra/"
    {{rmacro()}}

makina-haproxy-configuration-check:
  cmd.run:
    - name: /etc/init.d/haproxy checkconfig && echo "changed=no"
    - stateful: true
    - watch:
      - mc_proxy: ssl-certs-post-hook
      - mc_proxy: haproxy-post-conf-hook
    - watch_in:
      - mc_proxy: haproxy-pre-restart-hook


