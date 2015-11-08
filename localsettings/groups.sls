{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set ugs = salt['mc_usergroup.settings']() %}
include:
  - makina-states.localsettings.users.hooks
group-{{ugs.group}}:
  group.present:
    - name: {{ugs.group}}
    - gid: {{ugs.groupId}}
    - watch_in:
      - mc_proxy: groups-pre-hook
    - watch_in:
      - mc_proxy: groups-ready-hook
{% endif %}
