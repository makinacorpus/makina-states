{%- set circusSettings = salt['mc_circus.settings']() %}
{%- set venv = circusSettings['location'] + "/venv" %}
include:
  - makina-states.services.monitoring.circus.hooks

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
    - watch:
      - mc_proxy: circus-pre-install

{#- Install circus #}
circus-install-virtualenv:
  virtualenv.managed:
    - name: {{ venv }}
  pip.installed:
    - requirements: /etc/circus/requirements.txt
    - bin_env: {{ venv }}/bin/pip
    - watch:
      - virtualenv: circus-install-virtualenv
    - watch_in:
      - mc_proxy: circus-post-install
