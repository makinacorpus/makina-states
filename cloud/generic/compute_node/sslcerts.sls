include:
  - makina-states.cloud.generic.hooks

{# drop any configured ssl cert on the compute node #}
{% set data  = salt['mc_cloud_compute_node.cn_settings']().cnSettings %}
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
    - watch:
      - mc_proxy: cloud-sslcerts-pre
    - watch_in:
      - mc_proxy: cloud-sslcerts
{% endfor %}

