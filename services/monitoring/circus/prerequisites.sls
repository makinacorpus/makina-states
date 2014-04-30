{%- set circusSettings = salt['mc_circus.settings']() %}
{%- set venv = circusSettings['location'] + "/venv" %}
include:
  - makina-states.services.monitoring.circus.hooks

{#- Install circus #}
circus-install-virtualenv:
  virtualenv.managed:
    - name: {{ venv }}

circus-install-pkg:
  file.managed:
    - name: /etc/circus/requirements.txt
    - makedirs: true
    - source: ''
    - contents: |
                {{'\n                 '.join(circusSettings['requirements'])}}
    - user: root
    - group: root
    - mode: 750
  pip.installed:
    - requirements: /etc/circus/requirements.txt
    - bin_env: {{ venv }}/bin/pip
    - watch:
      - mc_proxy: circus-pre-install
      - file: circus-install-pkg
      - virtualenv: circus-install-virtualenv
    - watch_in:
      - file: circus-setup-conf
      - file: circus-setup-conf-include-directory
      - mc_proxy: circus-post-install
