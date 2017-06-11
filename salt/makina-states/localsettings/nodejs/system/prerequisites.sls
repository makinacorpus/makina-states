{# nodejs && yarn configuration #}
{% import "makina-states/_macros/h.jinja" as h with context %}
{% set settings = salt['mc_nodejs.settings']() %}
{% set cops = salt['mc_locations.settings']().cops %}
include:
  - makina-states.localsettings.nodejs.hooks
  - makina-states.controllers.corpusops
{% macro configure() %}
    - contents: |
         ---
         {% if settings.yarn_version_via_corpusops %}
         corpusops_localsettings_nodejs_version: '{{settings.version_via_corpusops}}'
         {% endif %}
         {% if settings.version_via_corpusops %}
         corpusops_localsettings_nodejs_yarn_version: '{{settings.yarn_version_via_corpusops}}'
         {% endif %}
{% endmacro %}
{{ h.install_via_cops('localsettings_nodejs', configure=configure) }}
