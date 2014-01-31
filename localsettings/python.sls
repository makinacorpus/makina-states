{#-
# Manage several python versions, see -standalone
#}
include:
  - makina-states.localsettings.pkgmgr
  - makina-states.localsettings.python-standalone

extend:
  makina-pythons-proxy:
    cmd.run:
      - require:
        - file: apt-sources-list
        - cmd: apt-update-after

