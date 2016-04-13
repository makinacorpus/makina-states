include:
  - makina-states.services.db.mysql.hooks
{%- set mysqlSettings = salt['mc_mysql.settings']() %}
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

mysql-msalt-pythonmysqldb-pip-install:
  pip.installed:
    - name: mysql-python==1.2.5
    - bin_env: /salt-venv/mastersalt/bin/pip
    - onlyif: test -e /salt-venv/mastersalt/bin/pip
    - require:
      - pkg: makina-mysql-pkgs
    - watch_in:
      - mc_proxy: mysql-post-install-hook

mysql-salt-pythonmysqldb-pip-install:
  pip.installed:
    - name: mysql-python==1.2.5
    - bin_env: /salt-venv/salt/bin/pip
    - onlyif: test -e /salt-venv/salt/bin/pip
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

mysqlservice-systemd-override-dir:
  file.directory:
    - makedirs: true
    - user: root
    - group: root
    - mode: 775
    - names:
      - /etc/systemd/system/mysql.service.d
    - watch_in:
      - mc_proxy: mysql-post-install-hook

mysqlservice-systemd-config-override:
  file.managed:
    - user: root
    - group: root
    - makedirs: true
    - mode: 664
    - name: /etc/systemd/system/mysql.service.d/override.conf
    - source: salt://makina-states/files/etc/systemd/system/overrides.d/mysql.conf
    - template: 'jinja'
    - require:
      - pkg: makina-mysql-pkgs
      - file: mysqlservice-systemd-override-dir
    - watch_in:
      - mc_proxy: mysql-post-install-hook

mysqlservice-systemd-reload-conf:
  cmd.run:
    - name: "systemctl daemon-reload"
    - onchanges:
      - file: mysqlservice-systemd-config-override
