#
# -  install ldap base packages
# -  integrate pam with LDAP
#
# Define your ldap settings to integrate with pam
# inside pillar
#
# {#
#
# makina.ldap.ldap_uri: ldaps://localhost:636/
# makina.ldap.ldap_base: dc=company,dc=org
# makina.ldap.ldap_passwd: ou=People,dc=company,dc=org?sub
# makina.ldap.ldap_shadow: ou=People,dc=company,dc=org?sub
# makina.ldap.ldap_group: ou=Group,dc=company,dc=org?sub
# makina.ldap.ldap_cacert: /etc/ssl/cacerts/cacert.pem (opt)
#
# #}

{% import "makina-states/_macros/ldap.jinja" as c with context %}
include:
  - makina-states.services.base.nscd

ldap-pkgs:
  pkg.installed:
    - names:
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
      - pkg: nslcd
      - file: nslcd
    - watch_in:
      - cmd: nscd-restart
  file.managed:
    - name: /etc/nslcd.conf
    - user: nslcd
    - group: nslcd
    - mode: '0600'
    - template: jinja
    - source: salt://makina-states/files/etc/nslcd.conf
    - require:
      - pkg: ldap-pkgs
      - file: ldap-cacerts-cert
    - defaults: {{ c.ldap_variables | yaml }}
    - watch_in:
      - cmd: nscd-restart

# add ldap tonsswitch
nslcd-nsswitch-conf:
  file.replace:
    - name: /etc/nsswitch.conf
    - search_only: ''
    - pattern: '^(passwd|group|shadow):\s*compat( ldap)*'
    - repl: '\1: compat ldap'
    - flags: ['MULTILINE', 'DOTALL']
    - watch_in:
      - cmd: nscd-restart

/etc/pam.d/common-session:
  file.append:
      - text: |
              # create homedir
              session required pam_mkhomedir.so skel=/etc/skel umask=0022

/etc/ldap.conf:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://makina-states/files/etc/ldap.conf
    - require:
      - pkg: ldap-pkgs
      - file: ldap-cacerts-cert
    - defaults: {{ c.ldap_variables | yaml }}

/etc/ldap/ldap.conf:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://makina-states/files/etc/ldap/ldap.conf
    - require:
      - pkg: ldap-pkgs
      - file: ldap-cacerts-cert
    - defaults: {{ c.ldap_variables | yaml }}

makina-certd:
  file.directory:
    - name: /etc/ssl/cacerts
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: True

ldap-cacerts-cert:
  file.managed:
    - name: /etc/ssl/cacerts/cacert.pem
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://makina-states/files/etc/ssl/cacerts/cacert.pem

