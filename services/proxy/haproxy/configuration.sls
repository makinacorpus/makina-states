{% import "makina-states/_macros/services.jinja" as services with context %}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set haproxySettings = services.haproxySettings %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.services.proxy.haproxy.service

makina-haproxy-configuration-check:
  cmd.run:
    - name: echo "" && echo "changed=yes"
    - stateful: true
    - watch:
      - mc_proxy: haproxy-post-conf-hook
    - watch_in:
      - mc_proxy: haproxy-pre-restart-hook

makina-haproxy-default:
  file.managed:
    - name: /etc/default/haproxy
    - source: salt://makina-states/files/etc/default/haproxy
    - user: root
    - group: root
    - mode: 755
    - template: jinja
    - defaults: {{haproxySettings.defaults | yaml}}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
