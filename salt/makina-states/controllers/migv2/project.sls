up_projects:
  - cmd.run: |
             cd /srv/makina-states
             bin/salt-call mc_project.link_projects
