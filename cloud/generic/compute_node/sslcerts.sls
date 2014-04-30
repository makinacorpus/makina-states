{# drop any configured ssl cert on the compute node #}
{% set data  = salt['mc_utils.json_load'](pillar.scnSettings) %}
{% for cert, content in data.ssl_certs %}
cpt-cloud-haproxy-cfg:
  file.managed:
    - name: /etc/ssl/cloud/certs/{{cert}}.crt
    - source: salt://makina-states/files/etc/cloud/certs/cert.crt
    - defaults:
      data: |
            {{salt['mc_utils.json_encode'](content)}}
    - user: root
    - group: root
    - mode: 644
    - makedirs: true
    - template: jinja
{% endfor %}
