include:
  - makina-states.services.backup.burp.hooks
  - makina-states.services.backup.burp.server.services
{% set data = salt['mc_burp.settings']() %}
{% set ssdata = data.server_conf %}

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
  file.managed:
    - name: /tmp/burpcagen.sh
    - source: salt://makina-states/files//etc/burp/cagen.sh
    - mode: 750
    - user: {{data.user}}
    - template: jinja
    - makedirs: true
    - group: {{data.group}}
  cmd.run:
    - name: /tmp/burpcagen.sh
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: etc-burp-CA
      - file: etc-burp-ca-gen
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
        client: server_conf
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
        client: server_conf
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

{% for f, fdata in {
  '/etc/logrotate.d/burp': {'mode': '755'},
  '/etc/default/burp-client': {'mode': '755'},
  '/etc/init.d/burp-client': {'mode': '755'},
  '/etc/burp/burp-client-restore.conf': {'mode': '750'},
  '/usr/bin/burp-restore': {'mode': '755'},
  '/etc/burp/timer_script': {'mode': '750'},
  '/etc/burp/notify_script': {'mode': '750'},
  '/etc/burp/burp.conf': {'mode': '750'},
  '/etc/burp/CA.cnf': {'mode': '750'},
}.items() %}
etc-burp-burp-client.{{client}}-conf-{{f}}:
  file.managed:
    - name: /etc/burp/clients/{{client}}/{{f}}
    - source: salt://makina-states/files/{{f}}
    - mode: {{fdata.mode}}
    - user: {{data.user}}
    - template: jinja
    - makedirs: true
    - group: {{data.group}}
    - defaults:
        client: {{client}}
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
        client: {{client}}
    - watch:
      - file: etc-burp-burp-client.{{client}}-backup-init
      - mc_proxy: burp-pre-conf-hook
    - watch_in:
      - mc_proxy: burp-post-conf-hook

etc-burp-{{client}}-ca-gen:
  file.managed:
    - name: /tmp/burpclient{{client}}cagen.sh
    - source: salt://makina-states/files//etc/burp/clientcagen.sh
    - mode: 750
    - defaults:
        client: {{client}}
    - user: {{data.user}}
    - template: jinja
    - makedirs: true
    - group: {{data.group}}
  cmd.run:
    - name: /tmp/burpclient{{client}}cagen.sh
    - watch:
      - file: etc-burp-{{client}}-ca-gen
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

burp-{{client}}-cleanupburpf:
  file.managed:
    - name: /etc/burp/clients/{{client}}/etc/burp/cleanup-burp-processes.sh
    - source: salt://makina-states/files/etc/burp/cleanup-burp-processes.sh
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-{{client}}-server-key
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-post-gen-sync

    - template: jinja
burp-{{client}}-cronjob:
  file.managed:
    - source: salt://makina-states/files/etc/burp/clients/client/etc/cron.d/burp
    - name: /etc/burp/clients/{{client}}/etc/cron.d/burp
    - makedirs: true
    - defaults:
        client: {{client}}
    - user: root
    - group: root
    - template: jinja
    - mode: 755
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-{{client}}-server-key
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-post-gen-sync


{% for i, jinja in [('cron.py', False), ('cron.sh', True)] %}
burp-{{client}}-cronjob-{{i}}:
  file.managed:
    - source: salt://makina-states/files/etc/burp/{{i}}
    - name: /etc/burp/clients/{{client}}/etc/burp/{{i}}
    - makedirs: true
    - defaults:
        client: {{client}}
    - user: root
    - group: root
    {% if jinja %}
    - template: jinja
    {% endif %}
    - mode: 755
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: burp-copy-{{client}}-server-key
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-post-gen-sync

{% endfor %}


{{client}}-install-burp-configuration:
  file.managed:
    - source: salt://makina-states/files/etc/burp/clients/client/sync.sh
    - name: /etc/burp/clients/{{client}}/sync.sh
    - mode: 0755
    - template: jinja
    - user: root
    - group: root
    - defaults:
        client: {{client}}
    - watch:
      - mc_proxy: burp-pre-conf-hook
      - file: etc-burp-burp-client.{{client}}-backup-init
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-post-restart-hook
      - mc_proxy: burp-post-gen-sync
{% endfor %}
