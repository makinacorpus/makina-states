{% set data = salt['mc_haproxy.settings']() %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.services.proxy.haproxy.service
  - makina-states.services.proxy.haproxy.userconf

makina-haproxy-configuration-check:
  cmd.run:
    - name: /etc/init.d/haproxy checkconfig && echo "changed=no"
    - stateful: true
    - watch:
      - mc_proxy: haproxy-post-conf-hook
    - watch_in:
      - mc_proxy: haproxy-pre-restart-hook

makina-haproxy-init:
  file.managed:
    - name: /etc/init.d/haproxy
    - makedirs: true
    - source: salt://makina-states/files/etc/init.d/haproxy
    - user: root
    - group: root
    - mode: 755
    - template: jinja
    - defaults:
        data: |
              {{salt['mc_utils.json_dump'](data)}}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook

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

{%set jdata =salt['mc_utils.json_dump'](data) %}
{% for f in ['/etc/logrotate.d/haproxy']%}

makina-haproxy-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - template: jinja
    - defaults:
      data: |
            {{jdata}}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
{% endfor %}
makina-haproxy-default:
  file.managed:
    - name: /etc/default/haproxy
    - source: salt://makina-states/files/etc/default/haproxy
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - template: jinja
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](data.defaults)}}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook

makina-haproxy-errors:
  file.recurse:
    - name: /etc/haproxy/errors
    - source: salt://makina-states/files/etc/haproxy/errors
    - dir_mode: 755
    - file_mode: 644
    - defaults: |
                {{salt['mc_utils.json_dump'](data)}}
    - makedirs: true
    - user: root
    - group: root
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook

makina-haproxy-cfg:
  file.managed:
    - name: {{data.config_dir}}/haproxy.cfg
    - source: salt://makina-states/files/etc/haproxy/haproxy.cfg
    - user: root
    - group: root
    - makedirs: true
    - mode: 644
    - template: jinja
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](data)}}
    - watch:
      - mc_proxy: haproxy-pre-conf-hook
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
