include:
  - makina-states.services.backup.burp.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.services.backup.burp.server.services
{% set data = salt['mc_burp.settings']() %}
{% set ssdata = data.server_conf %}
{% set sdata = salt['mc_utils.json_dump'](data.server_conf) %}

etc-burp-CA:
  file.directory:
    - names:
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

etc-burp-ca-gen:
  cmd.run:
    - name: >
            set -e &&
            rm -rf /etc/burp/CA &&
            if [ ! -e /etc/burp ];then mkdir -p /etc/burp;fi &&
            burp_ca --dhfile {{ssdata.ssl_dhfile}} &&
            burp_ca --ca_days 365000 -D 365000 -i --ca {{ssdata.ca_name}} &&
            burp_ca --key --request --name {{ssdata.fqdn}} &&
            burp_ca --days 365000 --batch --sign --ca {{ssdata.ca_name}} --name {{ssdata.fqdn}} &&
            touch /etc/burp/CA/.done
    - unless: test -e /etc/burp/CA/.done
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: etc-burp-CA
    - watch_in:
      - mc_proxy: burp-post-conf-hook

{% for f in ['/etc/logrotate.d/burp'] %}
etc-burp-burp-server.conf-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - mode: 644
    - user: {{data.user}}
    - template: jinja
    - makedirs: true
    - group: {{data.group}}
    - defaults:
      data: |
            {{sdata}}
    - watch:
      - cmd: etc-burp-ca-gen
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - file: burp-copy-ca-crt
{% endfor %}

{% for f in [
  '/etc/default/burp-server',
  '/etc/init.d/burp-server',
  '/etc/init.d/burp-restore',
  '/etc/default/burp-restore',
  '/etc/burp/burp-restore.conf',
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
      - cmd: etc-burp-ca-gen
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - file: burp-copy-ca-crt
{% endfor %}

burp-copy-ca-crt:
  file.copy:
    - name: {{ssdata.ssl_cert_ca}}
    - force: true
    - source: /etc/burp/CA/CA_{{ssdata.ca_name}}.crt
    - watch:
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-copy-server-key:
  file.copy:
    - force: true
    - name: {{ssdata.ssl_key}}
    - source: /etc/burp/CA/{{ssdata.fqdn}}.key
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-ca-crt
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-copy-server-cert:
  file.copy:
    - force: true
    - name: {{ssdata.ssl_cert}}
    - source: /etc/burp/CA/{{ssdata.fqdn}}.crt
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-server-key
    - watch_in:
      - mc_proxy: burp-post-conf-hook

{% for client, cdata in data['clients'].items() %}
{% set scdata = salt['mc_utils.json_dump'](cdata) %}
etc-burp-burp-client.{{client}}-backup-init:
  file.directory:
    - names:
      - {{data.server_conf.directory}}/{{client}}
      - /etc/burp/clients/{{client}}
    - makedirs: true
    - mode: 700
    - user: root
    - user: root
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-server-cert
    - watch_in:
      - mc_proxy: burp-post-conf-hook

{% for f in [
  '/etc/logrotate.d/burp',
  '/etc/default/burp-client',
  '/etc/init.d/burp-client',
  '/etc/burp/burp-client-restore.conf',
  '/usr/bin/burp-restore',
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
      - file: etc-burp-burp-client.{{client}}-backup-init
    - watch_in:
      - file: etc-burp-burp-client.{{client}}-confdir
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-post-gen-sync
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
      - file: etc-burp-burp-client.{{client}}-backup-init
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook

etc-burp-{{client}}-ca-gen:
  cmd.run:
    - name: >
            burp_ca --key --request --name {{cdata.cname}} &&
            burp_ca --days 365000 --batch --sign --ca {{ssdata.ca_name}} --name {{cdata.cname}} &&
            touch /etc/burp/CA/.{{client}}done
    - unless: |
              if test -e /etc/burp/CA/.{{client}}done;then exit 0;fi
              if test -e /etc/burp/CA/{{cdata.cname}}.crt;then exit 0;fi
              exit 1
    - watch:
      - file: etc-burp-burp-client.{{client}}-confdir
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-copy-{{client}}-ca-crt:
  file.copy:
    - force: true
    - name: /etc/burp/clients/{{client}}/{{ssdata.ssl_cert_ca}}
    - source: /etc/burp/CA/CA_{{ssdata.ca_name}}.crt
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - cmd: etc-burp-{{client}}-ca-gen
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-copy-{{client}}-server-cert:
  file.copy:
    - force: true
    - name: /etc/burp/clients/{{client}}/{{cdata.ssl_cert}}
    - source: /etc/burp/CA/{{cdata.cname}}.crt
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-{{client}}-ca-crt
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-copy-{{client}}-server-key:
  file.copy:
    - name: /etc/burp/clients/{{client}}/{{cdata.ssl_key}}
    - source: /etc/burp/CA/{{cdata.cname}}.key
    - force: true
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-{{client}}-server-cert
    - watch_in:
      - mc_proxy: burp-post-conf-hook

burp-{{client}}-cronjob:
  file.managed:
    - name: /etc/burp/clients/{{client}}/etc/burp/cleanup-burp-processes.sh
    - makedirs: true
    - contents: |
                #!/usr/bin/env bash
                MAILTO=""
                {{cdata.cron_periodicity}} {{cdata.cron_cmd}}
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-{{client}}-server-key
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-post-gen-sync 

burp-{{client}}-cronjob:
  file.managed:
    - name: /etc/burp/clients/{{client}}/etc/cron.d/burp
    - makedirs: true
    - contents: |
                #!/usr/bin/env bash
                MAILTO=""
                {{cdata.cron_periodicity}} {{cdata.cron_cmd}}
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-{{client}}-server-key
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-post-gen-sync

{{client}}-install-burp-configuration:
  file.managed:
    - name: /etc/burp/clients/{{client}}/sync.sh
    - mode: 0755
    - user: root
    - group: root
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: etc-burp-burp-client.{{client}}-backup-init
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-post-restart-hook
      - mc_proxy: burp-post-gen-sync
    - contents: |
            {{'#'}}!/usr/bin/env bash
            echo "Syncing {{client}}"
            {% for dir in ['burp', 'default', 'init.d', 'cron.d'] -%}rsync -azv -e '{{cdata['rsh_cmd']}}' /etc/burp/clients/{{client}}/etc/{{dir}}/ {{cdata['rsh_dst']}}:/etc/{{dir}}/ &&\
            {% endfor -%}
            /bin/true
            {% if not cdata.activated -%}
            {{cdata['ssh_cmd']}} rm -f /etc/cron.d/burp
            {% endif %}
            exit ${?}
{% endfor %}
{% endif %}
