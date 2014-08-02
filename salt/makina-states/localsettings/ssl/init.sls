{{ salt['mc_macros.register']('localsettings', 'ssl') }}
{# drop any configured ssl cert on the compute node #}
{% set certs = [] %}
{% set sacerts = [] %}
{% set socerts = [] %}
{% set sfcerts = [] %}
{% set sbcerts = [] %}
{% set skeys = [] %}

include:
  - makina-states.cloud.generic.hooks
  - makina-states.localsettings.ldap.ldap_conf
  - makina-states.localsettings.ssl.hooks

ssl-pkgs:
  pkg.latest:
    - pkgs:
      - ca-certificates
      - ssl-cert
    - watch_in:
      - mc_proxy: ssl-certs-pre-install
      - mc_proxy: ssl-certs-post-install

{% macro install_cert(cert, suf='') %}
{% set paths = salt['mc_ssl.get_cert_infos'](cert) %}
{% do certs.append(paths['crt']) %}
{% do skeys.append(paths['key']) %}
{% do socerts.append(paths['only']) %}
{% do sacerts.append(paths['auth']) %}
{% do sbcerts.append(paths['bundle']) %}
{% do sfcerts.append(paths['full']) %}
cpt-cert-{{cert}}-{{paths.domaincert}}-dirs{{suf}}:
  file.directory:
    - names:
      - /etc/ssl/cloud
      - /etc/ssl/cloud/certs
      - /etc/ssl/cloud/separate
    - user: root
    - group: ssl-cert
    - mode: 751
    - makedirs: true
    - watch:
      - mc_proxy: cloud-sslcerts-pre
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - mc_proxy: ssl-certs-clean-certs
      - mc_proxy: cloud-sslcerts
      - mc_proxy: ssl-certs-post-hook
{% for flav in ['crt', 'key',
                'authr', 'auth', 'bundle', 'full', 'only'] %}
cpt-cert-{{cert}}-{{paths.domaincert}}-{{flav}}{{suf}}:
  file.managed:
    - name: {{paths[flav]}}
    - source: salt://makina-states/files/etc/ssl/cloud/cert.{{flav}}.crt
    - defaults:
        certid: "{{paths.domaincert}}"
    - user: root
    - group: ssl-cert
    - mode: 640
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: cloud-sslcerts-pre
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - mc_proxy: ssl-certs-clean-certs
      - mc_proxy: cloud-sslcerts
      - mc_proxy: ssl-certs-post-hook
{% endfor%}
{% endmacro%}


{% set data  = salt['mc_ssl.settings']() %}
{% for cert in data.certificates %}
{{install_cert(cert)}}
{% endfor %}

{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set f='/tmp/cloudcerts.py' %}
cpt-certs-cleanup:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files{{f}}
    - defaults:
        f: {{f}}
        certs: |
               {{salt['mc_utils.json_dump'](certs)}}
    - user: root
    - group: root
    - mode: 700
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: cloud-sslcerts-pre
  cmd.run:
    - name: "{{f}}"
    - user: root
    - watch:
      - file: cpt-certs-cleanup
      - mc_proxy: cloud-sslcerts-pre
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - mc_proxy: cloud-sslcerts
      - mc_proxy: ssl-certs-post-hook
      - cmd: cpt-certs-install-openssl
{% endif %}
{#
cpt-certs-cleanup-openssl-cloud:
  cmd.run:
    - name: |
            set -e
            cd /etc/ssl/cloud/separate/
            find -name "*.key" -type f | egrep '[*]' | while read i
            do
              rm -vf "${i}"
            done
            find -name "*.crt" -type f | egrep '[*]' | while read i
            do
              rm -vf "${i}"
            done
    - onlyif: test -e /etc/ssl/cloud/separate
    - watch:
      - mc_proxy: cloud-sslcerts-pre
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - cmd: cpt-certs-cleanup-openssl-cloud
      - mc_proxy: ssl-certs-post-hook
#}
{% set f = '/tmp/sslcacerts.sh' %}
cpt-certs-install-openssl:
  file.managed:
    - name: "{{f}}"
    - source: "salt://makina-states/files{{f}}"
    - user: root
    - defaults:
      f: "{{f}}"
    - group: root
    - mode: 700
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: cloud-sslcerts-pre
  cmd.run:
    - name: "{{f}}"
    - onlyif: |
              set -e
              test $(ls /etc/ssl/cloud/separate/*crt|wc -c) -gt 0
              test -e /usr/local/share/ca-certificates
    - watch:
      - file: cpt-certs-install-openssl
      - mc_proxy: cloud-sslcerts-pre
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - mc_proxy: ssl-certs-post-hook
