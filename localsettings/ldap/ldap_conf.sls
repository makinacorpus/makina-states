include:
  - makina-states.localsettings.ldap.hooks

{% if salt['mc_controllers.allow_lowlevel_states']() %}
{%- set locs = salt['mc_locations.settings']() %}

localldap-dirs:
  file.directory:
    - names:
      - /etc/ldap
    - mode: 0755
    - user: root
    - grup: root
    - watch:
      - mc_proxy: localldap-post-install
    - watch_in:
      - mc_proxy: localldap-pre-conf


{{ locs.conf_dir }}-ldap-ldap.conf:
  file.managed:
    - name: {{ locs.conf_dir }}/ldap/ldap.conf
    - user: root
    - group: root
    - mode: '0644'
    - makedirs: true
    - template: jinja
    - source: salt://makina-states/files{{ locs.conf_dir }}/ldap/ldap.conf
    - watch:
      - mc_proxy: localldap-pre-conf
    - watch_in:
      - mc_proxy: users-pre-hook
      - mc_proxy: localldap-post-conf
{% endif %}
