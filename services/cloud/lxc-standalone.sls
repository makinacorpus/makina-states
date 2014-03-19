{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{% set localsettings = services.localsettings %}
{# this sls represent the salt controller part,
see also lxc-node for specific nodes installation #}
{% macro do(full=False) %}
{{- salt["mc_macros.register"]("services", "cloud.lxc") }}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.services.virt.lxc-hooks
  - makina-states.services.cloud.salt_cloud-hooks
  - makina-states.services.cloud.lxc-hooks
  {% if full %}
  - makina-states.services.cloud.salt_cloud
  {% else %}
  - makina-states.services.cloud.salt_cloud-standalone
  {% endif %}
  - makina-states.services.cloud.lxc-installconf
  - makina-states.services.cloud.lxc-installimages
  - makina-states.services.cloud.lxc-installnodes
{% endmacro %}
{{do(full=False)}}
