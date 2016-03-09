up_projects:
  - cmd.run: |
             cd /srv/makina-states
             for i in /srv/projects;do
               bin/salt-call --local mc_project.link $i
               bin/salt-call --local mc_project.sync_hooks $i
               bin/salt-call --local mc_project.sync_modules $i
             done
