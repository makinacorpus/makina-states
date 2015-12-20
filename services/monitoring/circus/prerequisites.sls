{%- set settings = salt['mc_circus.settings']() %}
{%- set venv = settings['location'] + "/venv" %}
include:
  - makina-states.services.monitoring.circus.hooks

circus-install-pkg:
  file.managed:
    - name: /etc/circus/requirements.txt
    - makedirs: true
    - source: ''
    - contents: |
                {{'\n'.join(settings['requirements'])|indent(18)}}
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
      - file: circus-install-pkg
    - watch_in:
      - mc_proxy: circus-post-install
