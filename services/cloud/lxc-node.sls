{% import "makina-states/_macros/services.jinja" as services with context %}
{% set nodetypes = services.nodetypes %}
{# post install is empty atm #}
{% if nodetypes.registry.is.devhost %}
include:
  - makina-states.services.cloud.lxc-devhost-sshkeys
  - makina-states.services.cloud.lxc-devhost-symlinks
{% endif %}
lxc-post-install:
  mc_proxy.hook: []
