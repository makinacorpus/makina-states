{{ salt['mc_macros.register']('controllers', 'salt') }}
include:
  - makina-states.controllers.requirements
  - makina-states.controllers.hooks
{%- set locs = salt['mc_locations.settings']() %}
{%- set settings = salt['mc_salt.settings']() %} 
{%- set bootsalt= '{0}/_scripts/boot-salt.sh'.format(settings.msr) %}
{% set pathid = salt['mc_utils.hash'](settings.msr, typ='md5') %}
{% for bin in ['ansible', 'ansible-playbook', 'salt-call', 'boot-salt.sh'] %}
salt-{{bin}}-bootsalt-link-bin:
  file.symlink:
    - name: /usr/local/bin/{{bin}}
    - target: {{ settings.msr }}/_scripts/{{bin}}
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
{% endfor %}
salt-restrict-conf:
  file.directory:
    - names:
      - {{ settings.msr }}/pillar
      - {{ settings.msr }}/etc
    - mode: 700
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
salt-crons:
  {% if not settings.cron_auto_sync %}
  file.absent:
    - name: /etc/cron.d/salt{{pathid}}
    - require:
      - mc_proxy: dummy-pre-salt-checkouts
      - cmd: update-makinastates-salta
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
  {% else %}
  file.managed:
    - name: /etc/cron.d/salt{{pathid}}
    - require:
      - mc_proxy: dummy-pre-salt-checkouts
      - cmd: update-makinastates-salta
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
    - source: ''
    - mode: 750
    - user: root
    - contents: |
                {% if settings.cron_auto_sync %}
                # salt code synchronization job
                {{settings.cron_sync_minute}} {{settings.cron_sync_hour}} * * * root   {{bootsalt}} --synchronize-code --quiet -C --no-colors
                {% endif %}
  {% endif %}
update-makinastates-salta:
  cmd.run:
    - name: {{bootsalt}} -C --no-colors --synchronize-code
    - require:
      - mc_proxy: dummy-pre-salt-checkouts
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart

update-makinastates-saltb:
  cmd.run:
    - name: |
            DO_SKIP_CHECKOUTS=y {{bootsalt}} -C \
              --no-makina-states --no-nodetype
    - require:
      - mc_proxy: dummy-pre-salt-checkouts
      - cmd: update-makinastates-salta
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
salt-salt-logrotate:
  file.managed:
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
    - template: jinja
    - name: {{ locs.conf_dir }}/logrotate.d/salt{{pathid}}.conf
    - source: salt://makina-states/files/etc/logrotate.d/salt.conf
    - require:
      - mc_proxy: dummy-pre-salt-checkouts
      - cmd: update-makinastates-salta
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
