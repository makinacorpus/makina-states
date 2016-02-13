{% import "makina-states/localsettings/npm/npm.sls" as base with context %}
{% set nodejs = salt['mc_nodejs.settings']() %}
include:
  - makina-states.localsettings.npm.hooks
{% for npmpackage, vers in nodejs.npmPackages %}
{% for ver in vers %}
{{npm.npmInstall(npmpackage, version=ver) }}
{% endfor %}
{% endfor %}
