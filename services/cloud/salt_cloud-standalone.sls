{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings= services.cloudSettings %}
{% set localsettings = services.localsettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{% macro do(full=False) %}
{{- salt["mc_macros.register"]("services", "cloud.salt_cloud") }}
include:
{% if full %}
  - makina-states.controllers
{% endif %}
  - makina-states.services.cloud.salt_cloud-hooks

{% if full %}
saltcloud-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - sshpass
    - require:
      - mc_proxy: salt-cloud-preinstall
{% endif %}
salt_cloud-dirs:
  file.directory:
    - names:
      - {{pvdir}}
      - {{pfdir}}
    - makedirs: true
    - user: root
    - group: {{localsettings.group }}
    - mode: 2770
    - require_in:
      - mc_proxy: salt-cloud-postinstall
    - require:
      - mc_proxy: salt-cloud-preinstall
{% endmacro %}
{{do(full=False)}}
