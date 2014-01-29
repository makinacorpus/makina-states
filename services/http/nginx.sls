{% import "makina-states/_macros/services.jinja" as services with context -%}
{% import "makina-states/_macros/salt.jinja" as saltmac with context -%}
{{ salt['mc_macros.register']('services', 'http.nginx') -}}


makina-nginx-pkgs:
  pkg.installed:
    - pkgs:
        - {{ services.nginxSettings.package }}

makina-nginx-minimal-default-vhost:
  file.managed:
    - require:
      - pkg: makina-nginx-pkgs
    - name: {{ services.nginxSettings.vhostdir }}/default
    - source:
      - salt://makina-states/files/etc/nginx/sites-available/default.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - watch_in:
       - service: makina-nginx-restart

#--- Configuration Check --------------------------------

# Configuration checker, always run before restart of graceful restart
makina-nginx-conf-syntax-check:
  cmd.script:
    - source: file://{{ saltmac.msr }}/_scripts/nginxConfCheck.sh
    - stateful: True
    - require:
      - pkg: makina-nginx-pkgs
    - require_in:
       - service: makina-nginx-restart
       - service: makina-nginx-reload

#--- MAIN SERVICE RESTART/RELOAD watchers --------------

makina-nginx-restart:
  service.running:
    - name: {{ services.nginxSettings.service }}
    - enable: True
    - watch:
      - pkg: makina-nginx-pkgs

makina-nginx-reload:
  service.running:
    - name: {{ services.nginxSettings.service }}
    - enable: True
    - reload: True
    - require:
      - pkg: makina-nginx-pkgs

{# Virtualhosts, here are the ones defined in pillar, if any ----------------
#
# We loop on VH defined in pillar nginx/virtualhosts, check the
# macro definition for the pillar dictionnary keys available. The
# virtualhosts key is set as the site name, and all keys are then
# added.
# pillar example:
# makina-states.services.http.nginx.virtualhosts:
#   example.com:
#     active: False
#     small_name: example
#     documentRoot: /srv/foo/bar/www
#   example.foo.com:
#     active: False
#     port: 8080
#     server_aliases:
#       - bar.foo.com
#
# Note that the best way to make a VH is not the pillar, but
# loading the macro as we do here and use virtualhost()) call
# in a state.
# Then use the pillar to alter your default parameters given to this call
-#}

{% from 'makina-states/services/http/nginx_macros.jinja' import virtualhost with context -%}
{% if 'virtualhosts' in services.nginxSettings -%}
{%   for site,siteDef in services.nginxSettings['virtualhosts'].iteritems() -%}
{%     do siteDef.update({'site': site}) -%}
{%     do siteDef.update({'nginxSettings': services.nginxSettings}) -%}
{{     virtualhost(**siteDef) -}}
{%   endfor -%}
{% endif -%}
