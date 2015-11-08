{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set settings = salt['mc_slapd.settings']() %}
include:
  - makina-states.services.dns.slapd.hooks
  - makina-states.services.dns.slapd.unregister

slapd-service-stop:
  service.dead:
    - name: {{settings.service_name}}
    - enable: false
    - watch:
      - mc_proxy: slapd-pre-restart
    - watch_in:
      - mc_proxy: slapd-post-restart 

slapd-pkgs:
  pkg.removed:
    - pkgs: [slapd]
    - watch:
      - mc_proxy: slapd-pre-install
    - watch_in:
      - mc_proxy: slapd-post-install

remove-gen-slapd-d-acls-schema:
  file.absent:
    - name: /etc/ldap/generate-acls.py 
    - watch:
      - mc_proxy: slapd-pre-install
    - watch_in:
      - mc_proxy: slapd-post-install 

remove-slapd-d-acls-schema:
  file.absent:
    - name: /etc/ldap/apply-acls.sh 
    - watch:
      - mc_proxy: slapd-pre-install
    - watch_in:
      - mc_proxy: slapd-post-install  
{%endif%}
