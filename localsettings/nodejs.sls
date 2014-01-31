{#-
#
# Install Node.js, see -standalone
#
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{%- set locs = localsettings.locations %}
{{ salt['mc_macros.register']('localsettings', 'nodejs') }}
{%- set npmPackages = localsettings.npmSettings.packages %}
include:
  - makina-states.localsettings.pkgmgr
  - makina-states.localsettings.pkgs
  - makina-states.localsettings.nodejs-standalone

extends:
  nodejs-proxy:
    cmd.run:
      - require:
        - file: apt-sources-list
        - cmd: apt-update-after
        - pkg: net-pkgs

