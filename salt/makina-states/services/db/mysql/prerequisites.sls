include:
  - makina-states.services.db.mysql.hooks
{%- set mysqlSettings = salt['mc_mysql.settings']() %}
{%- set venv = salt['mc_locations.settings']().venv %}
{#
# Note that python-mysqlDb binding is required for salt module to be loaded
#}
makina-mysql-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ mysqlSettings.packages.main }}
      - {{ mysqlSettings.packages.python }}
      - {{ mysqlSettings.packages.dev }}
    - watch:
      - mc_proxy: mysql-pre-install-hook
    - watch_in:
      - mc_proxy: mysql-post-install-hook

{#-
# Ensure mysqlDb python binding is available for the minion
# as it's needed to execute later mysql modules
#}

{#- retrocompat state #}
mysql-msalt-pythonmysqldb-pip-install:
  pip.installed:
    - name: mysql-python==1.2.5
    - bin_env: {{venv}}/bin/pip
    - onlyif: test -e {{venv}}/bin/pip
    - require:
      - pkg: makina-mysql-pkgs
    - watch_in:
      - mc_proxy: mysql-post-install-hook

mysql-salt-pythonmysqldb-pip-install:
  pip.installed:
    - name: mysql-python==1.2.5
    - bin_env: {{venv}}/bin/pip
    - onlyif: test -e {{venv}}/bin/pip
    - require:
      - pkg: makina-mysql-pkgs
    - watch_in:
      - mc_proxy: mysql-post-install-hook

mysql-salt-pythonmysqldb-pip-install-module-reloader:
  cmd.watch:
    - name: echo "Reloading Modules as mysql python was installed"
    {# WARNING: WE NEED TO REFRESH THE MYSQL MODULE #}
    - reload_modules: true
    - watch:
      - pip: mysql-salt-pythonmysqldb-pip-install
    - watch_in:
      - mc_proxy: mysql-post-install-hook
