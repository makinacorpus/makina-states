{% set vmname = pillar.mccloud_vmname %}
{% set target = pillar.mccloud_targetname %}
{% load_json as cloudSettings%}{{pillar.scloudSettings}}{%endload%}
lxc-initial-highstate:
  cmd.run:
    - name: ssh {{vmname}} {{cloudSettings.root}}/makina-states/_scripts/boot-salt.sh --initial-highstate
    - user: root
