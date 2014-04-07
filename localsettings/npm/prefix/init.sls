{% import "makina-states/localsettings/npm/npm.sls" as base with context %}
include:
  - makina-states.localsettings.npm.hooks
{% for ver, npmpackage in nodejs.npmPackages %}
{% if ver != 'system' %}
{{npm.npmInstall(npmpackage, version=version) }}
{% endif %}
{% endfor %}
