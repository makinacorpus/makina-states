{% set settings = salt['mc_pureftpd.settings']() %}
{% set pureftpdSettings = settings.conf %}

include:
  - makina-states.services.ftp.pureftpd.hooks

prereq-pureftpd:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - mc_proxy: ftpd-pre-installation-hook
    - watch_in:
      - mc_proxy: ftpd-post-installation-hook
    - pkgs:
      {%- if pureftpdSettings.LDAPConfigFile %}
      - pure-ftpd-ldap
      {%- elif pureftpdSettings.MySQLConfigFile %}
      - pure-ftpd-mysql
      {%- elif pureftpdSettings.PGSQLConfigFile %}
      - pure-ftpd-postgresql
      {%- else %}
      - pure-ftpd
      {%- endif %}
