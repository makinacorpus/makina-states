{% set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.localsettings.users-hooks
group-{{localsettings.group}}:
  group.present:
    - name: {{localsettings.group}}
    - gid: {{localsettings.groupId}}
    - watch_in:
      - mc_proxy: groups-pre-hook
    - watch_in:
      - mc_proxy: groups-ready-hook
