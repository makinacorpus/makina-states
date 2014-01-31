{#-
# Manage packages to install by default, see -standalone file
# We will here also include makina-states.localsettings.pkgmgr to install
# and configure any neccessary extra or core repository
#}
include:
  - makina-states.localsettings.pkgmgr
  - makina-states.localsettings.pkgs-standalone

extend:
  before-pkg-install-proxy:
    cmd.run:
      - require:
        - file: apt-sources-list
        - cmd: apt-update-after
