{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set cloudSettings= services.cloudSettings %}
{% set localsettings = services.localsettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{{- salt["mc_macros.register"]("services", "cloudcontroller") }}
include:
  - makina-states.services.cloud.cloudcontroller.hooks
salt_cloud-dirs:
  file.directory:
    - names:
      - {{pvdir}}
      - {{pfdir}}
    - makedirs: true
    - user: root
    - group: {{localsettings.group }}
    - mode: 2770
    - require:
      - mc_proxy: salt-cloud-preinstall
    - require_in:
      - mc_proxy: salt-cloud-postinstall
