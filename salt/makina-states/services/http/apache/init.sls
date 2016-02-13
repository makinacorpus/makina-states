# To register new vhosts, use the virtualhost macros inside the macros found in this folder
{% import "makina-states/services/http/apache/configuration.sls" as base with context %}
{{ salt['mc_macros.register']('services', 'http.apache') }}
{% set apacheSettings = base.apacheSettings%}
{% set apacheData = apacheSettings %}
include:
  - makina-states.services.http.common
  - makina-states.services.http.apache.prerequisites
  - makina-states.services.http.apache.configuration
  - makina-states.services.http.apache.services
{% set extend_switch_mpm = base.extend_switch_mpm %}
{% set default_vh_template_source = base.default_vh_template_source %}
{% set default_vh_in_template_source = base.default_vh_in_template_source %}
{% set minimal_index = base.minimal_index %}
{% set virtualhost = base.virtualhost %}
