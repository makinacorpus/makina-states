{% import "makina-states/_macros/h.jinja" as h with context %}
{%- set data = salt['mc_monitoring.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{% set dodl=True %}
{% if grains['os'] in ['Debian'] %}
{% if grains["osrelease"][0] < "6" %}
{% set dodl=False %}
{% endif %}
{% endif %}

install-nagios-plugins:
  pkg.installed:
    - pkgs:
      - nagios-plugins
      - nagios-plugins-contrib
      - libwww-perl
      {% if data.has_sysstat %}
      - sysstat
      {%endif %}
      {% if grains['os'] not in ['Debian'] %}
      - nagios-plugins-extra
      {% endif %}
      - libsnmp-base
      - libsnmp-perl
      - nagios-plugins-basic
      - libsnmp-dev
      - libsensors4
      - libcrypt-des-perl
      - libxml-xpath-perl
      - libsys-statistics-linux-perl
      {% if grains['oscodename'] in ['precise'] %}
      - nagios-plugins
      - nagios-plugins-basic
      - nagios-plugins-standard
      - nagios-plugins-extra
      - nagios-plugins-contrib
      {% else %}
      {% if grains['oscodename'] in ['Ubuntu'] %}
      {%  if grains['osrelease'] < '16.04' %}
      - nagios-plugins-openstack
      {%  endif %}
      {% endif %}
      {% if grains['os'] in ['Debian'] %}
      - libsnmp15
      {% else %}
      - libsnmp30
      {% endif %}
      {% endif %}

{% for f, mode in {
  '/etc/default/sysstat': 555,
  '/etc/cron.d/sysstat': 755,
  '/etc/sysstat/sysstat': 755,
  '/etc/sysstat/sysstat.ioconf': 755,

  }.items() %}
monitoring-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files{{f}}
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: {{mode}}
    - watch_in:
      - mc_proxy: monitoring-sysstat-svc
{% endfor %}

monitoring-sysstat-svc:
  mc_proxy.hook: []

{% macro smacro() %}
    - watch:
      - mc_proxy: monitoring-sysstat-svc
{% endmacro %}

{{h.toggle_service(prefix='monitoring-sysstat-svc',
                   service='sysstat',
                   after_macro=smacro,
                   action=data.has_sysstat) }}

ms-scripts-d:
  file.directory:
    - names:
      - /root/admin_scripts/nagios/
      - /usr/local/admin_scripts/nagios/
    - makedirs: true
    - mode: 755
{#
{% for g in [
'check_3ware_raid',
'check_3ware_raid_1_1',
'check_cciss-1.12',
'check_cron',
'check_ddos.pl',
'check_debian_packages',
'check_drbd',
'check_haproxy_stats.pl',
'check_md_raid',
'check_megaraid_sas',
'check_ntp_peer',
'check_ntp_time',
'check_postfix_mailqueue',
'check_postfixqueue.sh',
'check_raid.pl',
'check_rdiff',
'check_solr.py',
'check_supervisorctl.sh',
'check_swap',
'MANAGED_VIA_SALT',
] %}
{% endfor %}
#}

{% for i in ['misc', 'nagios'] %}
{{i}}-distributed-plugins-rec:
  cmd.run:
    - name: rsync -a {{locs.msr}}/files/usr/local/admin_scripts/{{i}}/ /usr/local/admin_scripts/{{i}}/
    - user: root
    - require:
      - file: ms-scripts-d
{% endfor %}
# old MC installs, do some symlinks
{% for g in [
'check_ntp_peer',
'check_ntp_time',
] %}
nagios-syms-{{g}}:
  file.symlink:
    - name: /root/{{g}}
    - target: /usr/local/admin_scripts/nagios/{{g}}
{% endfor %}
