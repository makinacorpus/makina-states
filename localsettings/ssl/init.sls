include:
  - makina-states.cloud.generic.hooks
  - makina-states.localsettings.ssl.hooks
{{ salt['mc_macros.register']('localsettings', 'ssl') }}
{# drop any configured ssl cert on the compute node #}
{% set data  = salt['mc_ssl.settings']() %}
{% set certs = [] %}
{% set socerts = [] %}
{% set sfcerts = [] %}
{% set sbcerts = [] %}
{% set skeys = [] %}
{% for cert, content in data.certificates.items() %}
{% do certs.append(cert+'.crt') %}
{% do   skeys.append(cert+'.key') %}
{% do socerts.append(cert+'.crt') %}
{% do sbcerts.append(cert+'.bundle.crt') %}
{% do sfcerts.append(cert+'.full.crt') %}
{% for flav in ['bundle', 'key', 'full', 'only'] %}
{% set ext = flav.endswith('key') and '.key' or '.crt'%}
{% if ext == '.crt' and flav not in ['only'] %}
{% set pref = '.' + flav %}
{% else %}
{% set pref = '' %}
{% endif %}
cpt-cert-{{cert}}-{{flav}}:
  file.managed:
    - name: /etc/ssl/cloud/separate/{{cert}}{{pref}}{{ext}}
    - source: salt://makina-states/files/etc/ssl/cloud/cert.{{flav}}.crt
    - defaults:
      certid: "{{cert}}"
    - user: root
    - group: root
    - mode: 640
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: cloud-sslcerts-pre
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - cmd: cpt-certs-cleanup
      - mc_proxy: cloud-sslcerts
      - mc_proxy: ssl-certs-post-hook
{% endfor%}
cpt-cert-{{cert}}-haproxy-dir:
  file.managed:
    - name: /etc/ssl/cloud/certs/{{cert}}.crt
    - source: salt://makina-states/files/etc/ssl/cloud/cert.crt
    - defaults:
      certid: "{{cert}}"
    - user: root
    - group: root
    - mode: 640
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: cloud-sslcerts-pre
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - cmd: cpt-certs-cleanup
      - mc_proxy: cloud-sslcerts
      - mc_proxy: ssl-certs-post-hook
{% endfor %}
{% if salt['mc_controllers.mastersalt_mode']() %}
{% set f='/tmp/cloudcerts.py' %}
cpt-certs-cleanup:
  file.managed:
    - name: {{f}}
    - user: root
    - group: root
    - mode: 700
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: cloud-sslcerts-pre
    - contents: |
                #!/usr/bin/env python
                import os, sys
                if os.path.exists('/etc/ssl/cloud/certs'):
                  os.chdir('/etc/ssl/cloud/certs')
                  certs = os.listdir('.')
                  [os.unlink(a) for a in certs if a not in {{certs}}]
                if os.path.exists('/etc/ssl/cloud/separate'):
                  sinfos = {{socerts}} + {{skeys}} + {{sfcerts}} + {{sbcerts}}
                  os.chdir('/etc/ssl/cloud/separate')
                  certs = os.listdir('.')
                  [os.unlink(a) for a in certs if a not in sinfos]
                os.unlink('{{f}}')
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
{% endif %}
