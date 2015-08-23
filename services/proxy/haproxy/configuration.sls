{% import "makina-states/_macros/h.jinja" as h with context %}
{% set data = salt['mc_haproxy.settings']() %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.services.proxy.haproxy.services

makina-haproxy-configuration-check:
  cmd.run:
    - name: /etc/init.d/haproxy checkconfig && echo "changed=no"
    - stateful: true
    - watch:
      - mc_proxy: ssl-certs-post-hook
      - mc_proxy: haproxy-post-conf-hook
    - watch_in:
      - mc_proxy: haproxy-pre-restart-hook

makina-haproxy-default-cfg:
  file.managed:
    - names:
    {% for i in ['backends', 'dispatchers', 'listeners', 'extra'] %}
      - {{data.config_dir}}/{{i}}/donotremoveme.cfg
    {% endfor %}
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - contents: ''
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
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

cpt-cloud-haproxy-cfg:
  file.absent:
    - name: {{salt['mc_haproxy.settings']().config_dir}}/extra/cloudcontroller.cfg
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
