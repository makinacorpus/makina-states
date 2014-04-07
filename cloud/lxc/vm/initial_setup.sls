{% set localsettings = salt['mc_localsettings.settings']() %}
{% set vmname = pillar.mccloud_svmname %}
{% set target = pillar.mccloud_stargetname %}
{% load_json as compute_node_settings%}{{pillar.scnSettings}}{%endload%}
{% load_json as data%}{{pillar.slxcVmData}}{%endload%}
{% load_json as cloudSettings%}{{pillar.scloudSettings}}{%endload%}
sysadmin-user-initial-password:
  cmd.run:
    - name: >
            for i in ubuntu root sysadmin;do
              echo "${i}:{{data.password}}" | chpasswd && touch /.initialspasses;
            done;
    - unless: test -e /.initialspasses
