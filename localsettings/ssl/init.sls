include:
  - makina-states.cloud.generic.hooks
{{ salt['mc_macros.register']('localsettings', 'ssl') }}
{# drop any configured ssl cert on the compute node #}
{% set data  = salt['mc_ssl.settings']() %}
{% set certs = [] %}
{% for cert, content in data.certificates.items() %}
{% do certs.append(cert+'.crt') %}
cpt-cert-{{cert}}-s:
  file.managed:
    - name: /etc/ssl/cloud/certs/{{cert}}.only.crt
    - source: salt://makina-states/files/etc/ssl/cloud/cert.only.crt
    - defaults:
      certid: "{{cert}}"
    - user: root
    - group: root
    - mode: 640
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: cloud-sslcerts-pre
    - watch_in:
      - mc_proxy: cloud-sslcerts 
cpt-cert-{{cert}}-o:
  file.managed:
    - name: /etc/ssl/cloud/certs/{{cert}}.key
    - source: salt://makina-states/files/etc/ssl/cloud/cert.key.crt
    - defaults:
      certid: "{{cert}}"
    - user: root
    - group: root
    - mode: 640
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: cloud-sslcerts-pre
    - watch_in:
      - mc_proxy: cloud-sslcerts  
cpt-cert-{{cert}}:
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
    - watch_in:
      - mc_proxy: cloud-sslcerts
{% endfor %}
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
                import os
                if os.path.exists('/etc/ssl/cloud/certs'):
                  os.chdir('/etc/ssl/cloud/certs')
                  certs = os.listdir('.')
                  [os.unlink(a) for a in certs if a not in {{certs}}]
                  os.unlink('{{f}}')
  cmd.run:
    - name: "{{f}}"
    - user: root
    - watch:
      - file: cpt-certs-cleanup
      - mc_proxy: cloud-sslcerts-pre
    - watch_in:
      - mc_proxy: cloud-sslcerts 
