# Default Virtualhost managment
{% import "makina-states/services/http/apache/macros.sls" as apache with context %}
include:
  - makina-states.services.http.common.default_vhost
  - makina-states.services.http.apache.hooks
  - makina-states.services.http.apache.services
{% set locs = salt['mc_locations.settings']() %}
{% set apacheSettings  = salt['mc_apache.settings']()%}
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
