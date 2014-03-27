{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
include:
  - makina-states.localsettings.users
  - makina-states.cloud.generic.hooks.controller
salt_cloud-dirs:
  file.directory:
    - names:
      - {{pvdir}}
      - {{pfdir}}
      - {{cloudSettings.root}}/{{cloudSettings.all_sls_dir}}
    - makedirs: true
    - user: root
    - group: {{localsettings.group }}
    - mode: 2770
    - require:
      - mc_proxy: cloud-generic-controller-pre-pre-deploy
    - require_in:
      - mc_proxy: cloud-generic-controller-pre-post-deploy
