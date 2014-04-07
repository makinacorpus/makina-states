{% set data = salt['mc_haproxy.settings']() %}
{% macro dispatcher(ldata, id=None) %}
{% do ldata.setdefault('name', id) %}
dispatcher-{{ldata.name}}-makina-haproxy-cfg:
  file.managed:
    - name: {{data.config_dir}}/dispatchers/{{id}}.cfg
    - source: salt://makina-states/files/etc/haproxy/dispatcher.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: true
    - template: jinja
    - defaults: {data: {{ldata|yaml}}}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
{% endmacro %}

{% macro listener(ldata, id=None) %}
{% do ldata.setdefault('name', id) %}
listener-{{ldata.name}}-makina-haproxy-cfg:
  file.managed:
    - name: {{data.config_dir}}/listeners/{{id}}.cfg
    - source: salt://makina-states/files/etc/haproxy/listener.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: true
    - template: jinja
    - defaults: {data: {{ldata|yaml}}}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
{% endmacro %}

{% macro frontend(ldata, id=None) %}
{% do ldata.setdefault('name', id) %}
frontend-{{ldata.name}}-makina-haproxy-cfg:
  file.managed:
    - name: {{data.config_dir}}/frontends/{{id}}.cfg
    - source: salt://makina-states/files/etc/haproxy/frontend.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: true
    - template: jinja
    - defaults: {data: {{ldata|yaml}}}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
{% endmacro %}

{% macro backend(ldata, id=None) %}
{% do ldata.setdefault('name', id) %}
backend-{{ldata.name}}-makina-haproxy-cfg:
  file.managed:
    - name: {{data.config_dir}}/backends/{{id}}.cfg
    - source: salt://makina-states/files/etc/haproxy/backend.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: true
    - template: jinja
    - defaults: {data: {{ldata|yaml}}}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
{% endmacro %}

{% for id, ldata in data.dispatchers.items() %}
{{ dispatcher(ldata, id=id)}}
{%endfor %}

{% for id, ldata in data.listeners.items() %}
{{ listener(ldata, id=id)}}
{%endfor %}

{% for id, ldata in data.backends.items() %}
{{ backend(ldata, id=id)}}
{%endfor %}

{% for id, ldata in data.frontends.items() %}
{{ frontend(ldata, id=id)}}
{%endfor %}
