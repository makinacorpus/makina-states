{% set data = salt['mc_haproxy.settings']() %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.services.proxy.haproxy.service

makina-haproxy-configuration-check:
  cmd.run:
    - name: /etc/init.d/haproxy checkconfig && echo "changed=no"
    - stateful: true
    - watch:
      - mc_proxy: haproxy-post-conf-hook
    - watch_in:
      - mc_proxy: haproxy-pre-restart-hook

makina-haproxy-default-cfg:
  file.managed:
    - names:
    {% for i in ['backends',
                 'dispatchers',
                 'listeners',
                 'extra'] %}
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

{% for f, fdata in data.configs.items() %}
{% set mode = fdata.get('mode', '644') %}
{{f}}-makina-haproxy-cfg:
  file.managed:
    - name: {{f}}
    - source: {{fdata.get('template', 'salt://makina-states/files'+f)}}
    - user: root
    - group: root
    - mode: {{mode}}
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
{% endfor %}
