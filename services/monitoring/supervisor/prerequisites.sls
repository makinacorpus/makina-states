{%- set supervisorSettings = salt['mc_supervisor.settings']() %}
{%- set venv = supervisorSettings['location'] + "/venv" %}
include:
  - makina-states.services.monitoring.supervisor.hooks

supervisor-install-pkg:
  file.managed:
    - name: /etc/supervisor/requirements.txt
    - makedirs: true
    - source: ''
    - contents: |
                {{'\n                 '.join(supervisorSettings['requirements'])}}
    - user: root
    - group: root
    - mode: 750
    - watch:
      - mc_proxy: supervisor-pre-install

{#- Install supervisor #}
supervisor-install-virtualenv:
  virtualenv.managed:
    - name: {{ venv }}
  pip.installed:
    - requirements: /etc/supervisor/requirements.txt
    - bin_env: {{ venv }}/bin/pip
    - watch:
      - virtualenv: supervisor-install-virtualenv
      - file: supervisor-install-pkg
    - watch_in:
      - mc_proxy: supervisor-post-install
