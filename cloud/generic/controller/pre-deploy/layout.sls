{% set cloudSettings = salt['mc_cloud_controller.settings']() %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
include:
  - makina-states.services.cloud.controller.hooks
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
