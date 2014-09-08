{#-
# pamldap configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/ldap.rst
#}

{{ salt['mc_macros.register']('localsettings', 'ldap') }}
{% if salt['mc_controllers.mastersalt_mode']() %}
{%- set locs = salt['mc_locations.settings']() %}

{% set ydata = salt['mc_utils.json_dump'](salt['mc_ldap.settings']()) %}

include:
  - makina-states.localsettings.nscd
  - makina-states.localsettings.users.hooks

{% set olddeb= False %}
{% set skip = False %}
{% if grains['os'] == 'Debian' -%}
{% if grains['osrelease'] < '6'  -%}
{% set skip = True %}
{% set olddeb = True %}
{% endif %}
{% endif %}
ldap-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - libpam-ldap{%if not olddeb%}d{%endif%}
      - libnss-ldapd
      - ldap-utils
      - libsasl2-modules
      - sasl2-bin
      - python-ldap
      {% if not skip %}
      - nslcd
      {%endif%}
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

{% if not olddeb %}
{{ locs.conf_dir }}-ldap.conf:
  file.absent:
    - name: {{ locs.conf_dir }}/ldap.conf
{% else %}
{# needed for old pam ldap, but not with libpam-ldapd and nslcd #}
{{ locs.conf_dir }}-ldap.conf:
  file.managed:
    - names:
      - {{ locs.conf_dir }}/ldap.conf
      - {{ locs.conf_dir }}/pam_ldap.conf
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://makina-states/files{{ locs.conf_dir }}/ldap.conf
    - require:
      - pkg: ldap-pkgs
      - file: ldap-cacerts-cert
    - defaults:
          data: |
                {{ydata}}
    - require_in:
      - mc_proxy: users-pre-hook
{% endif %}
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
    - makedirs: true
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://makina-states/files{{ locs.conf_dir }}/ssl/cacerts/cacert.pem
{% endif %}
# vim: set nofoldenable:
