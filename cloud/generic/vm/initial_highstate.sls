{% set vmname = pillar.mccloud_vmname %}
{% set target = pillar.mccloud_targetname %}
{% set cloudSettings = salt['mc_utils.json_load'](pillar.scloudSettings) %}
lxc-initial-highstate:
  cmd.run:
    - name: ssh {{vmname}} {{cloudSettings.root}}/makina-states/_scripts/boot-salt.sh --initial-highstate
    - user: root
