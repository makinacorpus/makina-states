{#-
# Manage dotdeb repo, see -standalone
#}
include:
  - makina-states.localsettings.pkgmgr
  - makina-states.localsettings.repository_dotdeb-standalone

extend:
  makina-dotdeb-proxy:
    cmd.run:
      - require:
        - file: apt-sources-list
        - cmd: apt-update-after
