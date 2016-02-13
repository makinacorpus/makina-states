{% set locs = salt['mc_locations.settings']() %}
{% set apacheSettings  = salt['mc_apache.settings']()%}

include:
  - makina-states.services.http.nginx.hooks
  - makina-states.services.http.apache.hooks

{# Replace defaut Virtualhost by a more minimal default Virtualhost [1]
# this is the directory
#}
makina-apache-default-vhost-directory:
  file.directory:
    - user: root
    - group: {{apacheSettings.httpd_user}}
    - mode: "2755"
    - makedirs: True
    - name: {{ locs.var_dir }}/www/default/
    - watch:
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: nginx-pre-conf-hook

{# Replace defaut Virtualhost by a more minimal default Virtualhost [2]
# this is the index.hml file
#}
makina-apache-default-vhost-index:
  file.managed:
    - name: {{ locs.var_dir }}/www/default/index.html
    - source:
      - salt://makina-states/files{{ locs.var_dir }}/www/default/default_vh.index.html
    - user: root
    - group: {{apacheSettings.httpd_user}}
    - makedirs: true
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
{% if salt['mc_nodetypes.is_devhost']() %}
    - context:
        mode: "dev"
{% endif %}
    # full service restart in case of changes
    - watch:
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: nginx-pre-conf-hook

{# Replace defaut Virtualhost by a more minimal default Virtualhost [3]
# remove index.html coming from package
#}
makina-apache-remove-package-default-index:
  file.absent:
    - name: {{ locs.var_dir }}/www/index.html
    - require:
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: makina-apache-post-inst
    - require_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: nginx-pre-conf-hook
