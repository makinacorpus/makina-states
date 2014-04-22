include:
  - makina-states.services.backup.burp.hooks
  - makina-states.services.backup.burp.server.services
{% set data = salt['mc_burp.settings']() %}
{% set ssdata = data.server_conf %}
{% set sdata = salt['mc_utils.json_dump'](data.server_conf) %}
etc-burp-ca-gen:
  cmd.run:
    - name: >
            rm -rf /etc/burp/CA &&
            burp_ca --dhfile {{ssdata.ssl_dhfile}} &&
            burp_ca --ca_days 365000 -D 365000 -i --ca {{ssdata.ca_name}} &&
            burp_ca --key --request --name {{ssdata.fqdn}} &&
            burp_ca --days 365000 --batch --sign --ca {{ssdata.ca_name}} --name {{ssdata.fqdn}} &&
            touch /etc/burp/CA/.done
    - unless: test -e /etc/burp/CA/.done
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - file: burp-copy-server-cert
      - file: burp-copy-server-key

{% for f in [
  '/etc/logrotate.d/burp',
  '/etc/default/burp-server',
  '/etc/init.d/burp-server',
  '/etc/burp/burp-server.conf',
  '/etc/burp/timer_script',
  '/etc/burp/notify_script',
  '/etc/burp/CA.cnf',
] %}
etc-burp-burp-server.conf-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - mode: 700
    - user: {{data.user}}
    - template: jinja
    - makedirs: true
    - group: {{data.group}}
    - defaults:
      data: |
            {{sdata}}
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook
{% endfor %}

burp-copy-server-cert:
  file.copy:
    - name: {{ssdata.ssl_cert}}
    - source: /etc/burp/CA/{{ssdata.fqdn}}.crt
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook

{#
burp-copy-server-client:
  file.copy:
    - name: /usr/sbin/burp-client
    - source: /usr/sbin/burp
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook
#}

burp-copy-ca-crt:
  file.copy:
    - name: {{ssdata.ssl_cert_ca}}
    - source: /etc/burp/CA/CA_{{ssdata.ca_name}}.crt
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-copy-server-key:
  file.copy:
    - name: {{ssdata.ssl_key}}
    - source: /etc/burp/CA/{{ssdata.fqdn}}.key
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook

#burp-ser-remove-packaging:
#  cmd.run:
#    - unless: test -h /etc/burp/burp.conf
#    - name: |
#            rm -f /etc/burp/burp.conf
#            ln -s /etc/burp/burp-server.conf /etc/burp/burp.conf
#    - watch:
#      - mc_proxy: burp-pre-conf-hook
#    - watch_in:
#      - mc_proxy: burp-post-conf-hook
#  file.absent:
#    - names:
#      - /etc/init.d/burp
#    - watch:
#      - mc_proxy: burp-pre-conf-hook
#    - watch_in:
#      - mc_proxy: burp-post-conf-hook
#  service.dead:
#    - name: burp
#    - watch:
#      - mc_proxy: burp-pre-conf-hook
#    - watch_in:
#      - mc_proxy: burp-post-conf-hook
#
etc-burp-CA:
  file.directory:
    - names:
      - /etc/burp/CA
      - {{data.server_conf.clientconfdir }}
      - {{data.server_conf.directory }}
    - mode: 700
    - makedirs: true
    - user: {{data.user}}
    - group: {{data.group}}
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook

{% for client, cdata in data['clients'].items() %}
{% set scdata = salt['mc_utils.json_dump'](cdata) %}
{% for f in [
  '/etc/logrotate.d/burp',
  '/etc/default/burp-client',
  '/etc/init.d/burp-client',
  '/etc/burp/timer_script',
  '/etc/burp/notify_script',
  '/etc/burp/burp.conf',
  '/etc/burp/CA.cnf',
] %}
etc-burp-burp-client.{{client}}-conf-{{f}}:
  file.managed:
    - name: /etc/burp/clients/{{client}}/{{f}}
    - source: salt://makina-states/files/{{f}}
    - mode: 700
    - user: {{data.user}}
    - template: jinja
    - makedirs: true
    - group: {{data.group}}
    - defaults:
      data: |
            {{scdata}}
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook
{% endfor %}

etc-burp-burp-client.{{client}}-confdir:
  file.managed:
    - name: /etc/burp/clientconfdir/{{cdata.cname}}
    - source: salt://makina-states/files/etc/burp/clientconfdir/client
    - mode: 700
    - user: {{data.user}}
    - template: jinja
    - makedirs: true
    - group: {{data.group}}
    - defaults:
      data: |
            {{scdata}}
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook

etc-burp-{{client}}-ca-gen:
  cmd.run:
    - name: >
            burp_ca --key --request --name {{cdata.cname}} &&
            burp_ca --days 365000 --batch --sign --ca {{ssdata.ca_name}} --name {{cdata.cname}} &&
            touch /etc/burp/CA/.{{client}}done
    - unless: test -e /etc/burp/CA/.{{client}}done
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - cmd: etc-burp-ca-gen
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - file: burp-copy-server-cert
      - file: burp-copy-server-key

burp-copy-{{client}}-ca-crt:
  file.copy:
    - name: /etc/burp/clients/{{client}}/{{ssdata.ssl_cert_ca}}
    - source: /etc/burp/CA/CA_{{ssdata.ca_name}}.crt
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: etc-burp-burp-client.{{client}}-confdir
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-copy-{{client}}-server-cert:
  file.copy:
    - name: /etc/burp/clients/{{client}}/{{cdata.ssl_cert}}
    - source: /etc/burp/CA/{{cdata.cname}}.crt
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - cmd: etc-burp-{{client}}-ca-gen
      - file: etc-burp-burp-client.{{client}}-confdir
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-copy-{{client}}-server-key:
  file.copy:
    - name: /etc/burp/clients/{{client}}/{{cdata.ssl_key}}
    - source: /etc/burp/CA/{{cdata.cname}}.key
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: etc-burp-burp-client.{{client}}-confdir
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-{{client}}-cronjob:
  file.managed:
    - name: /etc/burp/clients/{{client}}/etc/cron.d/burp
    - makedirs: true
    - contents: |
                MAILTO=""
                {{cdata.cron_periodicity}} {{cdata.cron_cmd}}
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: etc-burp-burp-client.{{client}}-confdir
    - watch_in:
      - mc_proxy: burp-post-conf-hook
{% endfor %}
