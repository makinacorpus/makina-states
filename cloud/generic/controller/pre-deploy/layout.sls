{% set cloudSettings = salt['mc_cloud_controller.settings']() %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
include:
  - makina-states.cloud.generic.hooks
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
      - mc_proxy: cloud-generic-pre-pre-deploy
    - require_in:
      - mc_proxy: cloud-generic-pre-post-deploy
