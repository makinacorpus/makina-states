# Default Virtualhost managment
{% import "makina-states/services/http/apache/macros.sls" as apache with context %}
include:
  - makina-states.services.http.apache.hooks
  - makina-states.services.http.apache.services
{% set locs = salt['mc_locations.settings']() %}
{% set apacheSettings  = salt['mc_apache.settings']()%}

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
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf

{# Replace defaut Virtualhost by a more minimal default Virtualhost [2]
# this is the index.hml file
#}
makina-apache-default-vhost-index:
  file.managed:
    - name: {{ locs.var_dir }}/www/default/index.html
    - source:
      - salt://makina-states/files{{ locs.var_dir }}/www/default/default_vh.index.html
    - user: root
    - makedirs: true
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
    - context:
        mode: "dev"
{% endif %}
    # full service restart in case of changes
    - watch:
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf

{# Replace defaut Virtualhost by a more minimal default Virtualhost [3]
# remove index.html coming from package
#}
makina-apache-remove-package-default-index:
  file.absent:
    - name : {{ locs.var_dir }}/www/index.html
    - watch:
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf

{# Replace defaut Virtualhost by a more minimal default Virtualhost [4]
# this is the virtualhost definition
#}
makina-apache-minimal-default-vhost-remove-olds:
  file.absent:
    - names:
      - {{ apacheSettings.evhostdir }}/default
      - {{ apacheSettings.evhostdir }}/default-ssl
      - {{ apacheSettings.vhostdir }}/default
      - {{ apacheSettings.vhostdir }}/default-ssl
    - watch_in:
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
