{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
include:
  - makina-states.localsettings.users
  - makina-states.cloud.generic.genssh
salt_cloud-dirs:
  file.directory:
    - names:
      - {{pvdir}}
      - {{pfdir}}
      - {{cloudSettings.root}}/{{cloudSettings.all_sls_dir}}
    - makedirs: true
    - user: root
    - group: {{salt['mc_usergroup.settings']().group }}
    - mode: 2770
