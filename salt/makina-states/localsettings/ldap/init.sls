{#-
# pamldap configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/ldap.rst
#}

{{ salt['mc_macros.register']('localsettings', 'ldap') }}
{%- set locs = salt['mc_locations.settings']() %}

include:
  - makina-states.localsettings.ldap.hooks
  - makina-states.localsettings.ldap.ldap_conf
  - makina-states.localsettings.nscd
  - makina-states.localsettings.users.hooks

{% set settings = salt['mc_ldap.settings']() %}

{% set olddeb= False %}
{% set skip = False %}
{% if grains['os'] == 'Debian' -%}
{% if grains['osrelease'] < '6'  -%}
{% set skip = True %}
{% set olddeb = True %}
{% endif %}
{% endif %}
{% if not settings.enabled %}
ldap-pkgs-purge:
  pkg.purged:
    - pkgs:
      - libpam-ldap{%if not olddeb%}d{%endif%}
      - libnss-ldapd
      - nslcd
    - watch:
      - mc_proxy: localldap-pre-install
    - watch_in:
      - mc_proxy: localldap-post-install
{% endif %}
ldap-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      {% if settings.enabled %}
      - libpam-ldap{%if not olddeb%}d{%endif%}
      - libnss-ldapd
      {% if not skip %}
      - nslcd
      {%endif%}
      {% endif %}
      - ldap-utils
      - libsasl2-modules
      - sasl2-bin
      - python-ldap
      {% if grains['os_family'] == 'Debian' -%}
      - libldap2-dev
      - libsasl2-dev
      {%- endif %}
    - watch:
      - mc_proxy: localldap-pre-install
    - watch_in:
      - mc_proxy: localldap-post-install

nslcd:
  {% if settings.enabled %}
  service.running:
    - enable: True
  {% else %}
  service.dead:
    - enable: False
  {% endif %}
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
      - mc_proxy: localldap-pre-conf
    - watch_in:
      - cmd: nscd-restart
      - mc_proxy: localldap-post-conf
    - require_in:
      - mc_proxy: users-pre-hook

# add ldap tonsswitch
nslcd-nsswitch-conf:
  file.replace:
    - require_in:
      - mc_proxy: users-pre-hook
    - name: {{ locs.conf_dir }}/nsswitch.conf
    - pattern: '^(?P<title>passwd|group|shadow):\s*compat( ldap)*'
    {% if settings.enabled %}
    - repl: '\g<title>: compat ldap'
    {% else %}
    - repl: '\g<title>: compat'
    {% endif %}
    - flags: ['MULTILINE', 'DOTALL']
    - watch:
      - mc_proxy: localldap-pre-conf
    - watch_in:
      - mc_proxy: localldap-post-conf
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
    - watch:
      - mc_proxy: localldap-pre-conf
    - watch_in:
      - mc_proxy: localldap-post-conf
    - require:
      - pkg: ldap-pkgs
      - file: ldap-cacerts-cert
    - require_in:
      - mc_proxy: users-pre-hook

{% endif %}
makina-certd:
  file.directory:
    - name: {{ locs.conf_dir }}/ssl/cacerts
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: True
    - require_in:
      - mc_proxy: users-pre-hook
    - watch:
      - mc_proxy: localldap-pre-conf
    - watch_in:
      - mc_proxy: localldap-post-conf

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
    - watch:
      - mc_proxy: localldap-pre-conf
    - watch_in:
      - mc_proxy: localldap-post-conf
# vim: set nofoldenable:
