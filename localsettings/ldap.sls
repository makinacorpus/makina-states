{#-
# pamldap configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/ldap.rst
#}

{{ salt['mc_macros.register']('localsettings', 'ldap') }}
{%- set locs = salt['mc_locations.settings']() %}

{% set ydata = salt['mc_utils.json_dump'](salt['mc_ldap.settings']()) %}

include:
  - makina-states.localsettings.nscd
  - makina-states.localsettings.users-hooks

ldap-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - libpam-ldapd
      - libnss-ldapd
      - ldap-utils
      - libsasl2-modules
      - sasl2-bin
      - python-ldap
      - nslcd
      {% if grains['os_family'] == 'Debian' -%}
      - libldap2-dev
      - libsasl2-dev
      {%- endif %}

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
    - defaults:
      data: |
            {{ydata}}
    - watch_in:
      - cmd: nscd-restart
    - require_in:
      - mc_proxy: users-pre-hook

# add ldap tonsswitch
nslcd-nsswitch-conf:
  file.replace:
    - require_in:
      - mc_proxy: users-pre-hook
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
  file.absent:
    - name: {{ locs.conf_dir }}/ldap.conf
{# needed for old pam ldap, but not with libpam-ldapd and nslcd
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
    - defaults: |
                {{ydata}}
    - require_in:
      - mc_proxy: users-pre-hook
#}
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
    - defaults:
      data: |
            {{ydata}}
    - require_in:
      - mc_proxy: users-pre-hook

makina-certd:
  file.directory:
    - name: {{ locs.conf_dir }}/ssl/cacerts
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: True
    - require_in:
      - mc_proxy: users-pre-hook

ldap-cacerts-cert:
  file.managed:
    - require_in:
      - mc_proxy: users-pre-hook
    - name: {{ locs.conf_dir }}/ssl/cacerts/cacert.pem
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://makina-states/files{{ locs.conf_dir }}/ssl/cacerts/cacert.pem
# vim: set nofoldenable:
