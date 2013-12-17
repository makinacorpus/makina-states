#
# -  install ldap base packages
# -  integrate pam with LDAP
#
# Define your ldap settings to integrate with pam
# inside pillar
#
# {#
#
#  ldap-default-settings:
#    enabled: true|false
#    ldap_uri: ldaps://localhost:636/
#    ldap_base: dc=company,dc=org
#    ldap_passwd: ou=People,dc=company,dc=org?sub
#    ldap_shadow: ou=People,dc=company,dc=org?sub
#    ldap_group: ou=Group,dc=company,dc=org?sub
#    ldap_cacert: /etc/ssl/cacerts/cacert.pem (opt)
#
# #}

{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}

{{ localsettings.register('ldap') }}
{% set locs = localsettings.locations %}

include:
  - {{ localsettings.statesPref }}nscd

ldap-pkgs:
  pkg.installed:
    - pkgs:
      - libpam-ldap
      - libnss-ldapd
      - ldap-utils
      - libsasl2-modules
      - sasl2-bin
      - python-ldap
      - nslcd
      {% if grains['os_family'] == 'Debian' -%}
      - libldap2-dev
      - libsasl2-dev
      {% endif %}

nslcd:
  service.running:
    - enable: True
    - watch:
      - pkg: ldap-pkgs
      - file: nslcd
    - watch_in:
      - cmd: nscd-restart
  file.managed:
    - name: {{ locs.conf_dir }}/nslcd.conf
    - user: nslcd
    - group: nslcd
    - mode: '0600'
    - template: jinja
    - source: salt://makina-states/files{{ locs.conf_dir }}/nslcd.conf
    - require:
      - pkg: ldap-pkgs
      - file: ldap-cacerts-cert
    - defaults: {{ services.ldapVariables | yaml }}
    - watch_in:
      - cmd: nscd-restart

# add ldap tonsswitch
nslcd-nsswitch-conf:
  file.replace:
    - name: {{ locs.conf_dir }}/nsswitch.conf
    - search_only: ''
    - pattern: '^(passwd|group|shadow):\s*compat( ldap)*'
    - repl: '\1: compat ldap'
    - flags: ['MULTILINE', 'DOTALL']
    - watch_in:
      - cmd: nscd-restart

{{ locs.conf_dir }}-pam.d-common-session:
  file.append:
      - name: {{ locs.conf_dir }}/pam.d/common-session
      - text: |
              # create homedir
              session required pam_mkhomedir.so skel={{ locs.conf_dir }}/skel umask=0022

{{ locs.conf_dir }}-ldap.conf:
  file.managed:
    - name: {{ locs.conf_dir }}/ldap.conf
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://makina-states/files{{ locs.conf_dir }}/ldap.conf
    - require:
      - pkg: ldap-pkgs
      - file: ldap-cacerts-cert
    - defaults: {{ services.ldapVariables | yaml }}

{{ locs.conf_dir }}-ldap-ldap.conf:
  file.managed:
    - name: {{ locs.conf_dir }}/ldap/ldap.conf
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://makina-states/files{{ locs.conf_dir }}/ldap/ldap.conf
    - require:
      - pkg: ldap-pkgs
      - file: ldap-cacerts-cert
    - defaults: {{ services.ldapVariables | yaml }}

makina-certd:
  file.directory:
    - name: {{ locs.conf_dir }}/ssl/cacerts
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: True

ldap-cacerts-cert:
  file.managed:
    - name: {{ locs.conf_dir }}/ssl/cacerts/cacert.pem
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://makina-states/files{{ locs.conf_dir }}/ssl/cacerts/cacert.pem

# vim: set nofoldenable:
