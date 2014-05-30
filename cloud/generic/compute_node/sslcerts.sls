{# drop any configured ssl cert on the compute node #}
{% set data  = salt['mc_utils.json_load'](pillar.scnSettings) %}
{% for cert, content in data.cn.ssl_certs %}
cpt-cert-{{cert}}:
  file.managed:
    - name: /etc/ssl/cloud/certs/{{cert}}.crt
    - source: salt://makina-states/files/etc/ssl/cloud/cert.crt
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](content)}}
    - user: root
    - group: root
    - mode: 640
    - makedirs: true
    - template: jinja
{% endfor %}

cloud-sslcerts:
  mc_proxy.hook: []
