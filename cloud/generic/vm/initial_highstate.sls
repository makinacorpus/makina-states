{% set vmname = pillar.mccloud_vmname %}
{% set target = pillar.mccloud_targetname %}
{% set cloudSettings = salt['mc_utils.json_load'](pillar.scloudSettings) %}
vm-initial-highstate:
  cmd.run:
    - name: "ssh -o\"ProxyCommand=ssh {{target}} nc -w300 {{vmname}} 22\" footarget {{cloudSettings.root}}/makina-states/_scripts/boot-salt.sh --initial-highstate"
    - user: root
