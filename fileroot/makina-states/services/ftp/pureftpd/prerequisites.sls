{% set settings = salt['mc_pureftpd.settings']() %}
{% set pureftpdSettings = settings.conf %}

include:
  - makina-states.services.ftp.pureftpd.hooks

{% set pkgssettings = salt['mc_pkgs.settings']() %}
pure-ftpd-clean:
  cmd.run:
    - name: sed -i -e "/ftp/d" /etc/apt/sources.list.d/pure-ftpd.list && echo "changed=false"
    - stateful: true
    - onlyif: |
              if test -e /etc/apt/sources.list.d/pure-ftpd.list;then
                grep -q pure-ftpd /etc/apt/sources.list.d/pure-ftpd.list;exit ${?};
              fi
              exit 1
    - watch:
      - mc_proxy: ftpd-pre-installation-hook
    - watch_in:
      - pkgrepo: pure-ftpd-base
      - cmd: pure-ftpd-base
{# clean typo in old confs #}
pure-ftpd-base:
  cmd.run:
    - name: sed -re "/corpusops/d" -i /etc/apt/sources.list.d/pure-ftpd.list
    - onlyif: grep -q makinacorpus /etc/apt/sources.list.d/pure-ftpd.list
    - watch:
      - mc_proxy: ftpd-pre-installation-hook
    - watch_in:
      - pkgrepo: pure-ftpd-base
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - humanname: pure-ftpd ppa
    - name: deb http://ppa.launchpad.net/corpusops/pure-ftpd/ubuntu {{pkgssettings.udist}} main
    - dist: {{pkgssettings.udist}}
    - file: /etc/apt/sources.list.d/pure-ftpd.list
    - keyid: 4420973F
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: ftpd-pre-installation-hook
    - watch_in:
      - pkg: prereq-pureftpd

prereq-pureftpd:
  pkg.latest:
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
