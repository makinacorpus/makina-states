{% set cloudSettings = salt['mc_cloud.settings']()%}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
remove_old_saltcloud_providers_lxc_salt:
  file.absent:
    - names:
      - {{pvdir}}/makinastates_lxc.conf
      - {{pfdir}}/makinastates_lxc.conf
