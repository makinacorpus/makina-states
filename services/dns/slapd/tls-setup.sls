{% set settings = salt['mc_slapd.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}
include:
  - makina-states.services.dns.slapd.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
slapd-etc-ssl-cert:
  file.managed:
    - name: /usr/local/share/ca-certificates/{{settings.cert_domain}}.crt
    - contents: |
                {{settings.tls_cert.replace('\n',
'\n                ')}}
    - makedirs: true
    - mode: 644
    - user: {{settings.user}}
    - group: {{settings.user}}
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
      - cmd: slapd-etc-ssl-key-register

slapd-etc-ssl-cacert:
  file.managed:
    - name: /usr/local/share/ca-certificates/cacert{{settings.cert_domain}}.crt
    - contents: |
                {{settings.tls_cacert.replace('\n',
'\n                ')}}
    - makedirs: true
    - mode: 644
    - user: {{settings.user}}
    - group: {{settings.user}}
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
      - cmd: slapd-etc-ssl-key-register

slapd-etc-ssl-key-dir:
  file.directory:
    - name: /etc/ssl/custom
    - makedirs: true
    - mode: 755
    - user: root
    - group: root
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf

slapd-etc-ssl-key:
  file.managed:
    - name: /etc/ssl/custom/{{settings.cert_domain}}.key
    - contents: |
                {{settings.tls_key.replace('\n',
'\n                ')}}
    - makedirs: true
    - mode: 640
    - user: {{settings.user}}
    - group: {{settings.user}}
    - watch:
      - file: slapd-etc-ssl-key-dir
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
      - cmd: slapd-etc-ssl-key-register

slapd-etc-ssl-key-register:
  cmd.run:
    - name: update-ca-certificates
    - use_vt: true
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
{% endif %}
