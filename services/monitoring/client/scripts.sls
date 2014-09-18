install-nagios-plugins:
  pkg.installed:
    - pkgs:
      - nagios-plugins
      - nagios-plugins-contrib
      - nagios-plugins-extra
      - nagios-plugins-openstack
      - libcrypt-des-perl

ms-scripts-d:
  file.directory:
    - names:
      - /root/admin_scripts/nagios/
    - makedirs: true
    - mode: 700
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
  file.recurse:
    - name: /usr/local/admin_scripts/{{i}}/
    - source: salt://makina-states/files/usr/local/admin_scripts/{{i}}/
    - user: root
    - group: root
    - makedirs: true
    - include_pat: '*'
    - file_mode: 755
    - dir_mode: 755
    - template: jinja
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
    - target: /root/admin_scripts/nagios/{{g}}
{% endfor %}
