{% set locs = salt['mc_locations.settings']() %}
up_projects:
  - cmd.run: |
             cd {{data.msr}}
             bin/salt-call mc_project.link_projects
