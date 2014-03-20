{#- Postfix SMTP Server managment #}
{% macro do(full=True) %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'proxy.haproxy') }}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set haproxySettings = services.haproxySettings %}
{% set locs = localsettings.locations %}
include:
  - makina-states.services.proxy.haproxy-hooks

{% if full %}
haproxy-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - haproxy
    - watch:
      - mc_proxy: haproxy-pre-install-hook
    - watch_in:
      - mc_proxy: haproxy-post-install-hook
{% endif %}

{#
makina-haproxy-virtual:
  file.managed:
    - name: {{ locs.conf_dir }}/haproxy/virtual
    - source: salt://makina-states/files/etc/haproxy/virtual
    - user: root
    - template: jinja
    - defaults: {{haproxySettings|yaml}}
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
#}

makina-haproxy-configuration-check:
  cmd.run:
    - name: echo "" && echo "changed=yes"
    - stateful: True
    - watch:
      - mc_proxy: haproxy-post-conf-hook
    - watch_in:
      - mc_proxy: haproxy-pre-restart-hook

makina-haproxy-service:
  service.running:
    - name: haproxy
    - enable: True
    - watch_in:
      - mc_proxy: haproxy-post-restart-hook
    - watch:
      - mc_proxy: haproxy-pre-restart-hook
{% endmacro %}
{{ do(full=False) }}
