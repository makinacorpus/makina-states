{% set localsettings = salt['mc_localsettings.settings']() %}
{% set vmname = pillar.mccloud_svmname %}
{% set target = pillar.mccloud_stargetname %}
{% set compute_node_settings = salt['mc_utils.json_load'](pillar.scnSettings) %}
{% set data = salt['mc_utils.json_load'](pillar.slxcVmData) %}
{% set cloudSettings = salt['mc_utils.json_load'](pillar.scloudSettings) %}
sysadmin-user-initial-password:
  cmd.run:
    - name: >
            for i in ubuntu root sysadmin;do
              echo "${i}:{{data.password}}" | chpasswd && touch /.initialspasses;
            done;
    - unless: test -e /.initialspasses
