{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{# see makina-states.localsettings.standalone #}
include:
  - makina-states.localsettings.standalone

{# POST INSTALLATION ORCHESTRATION STUFF #}
{{localsettings.autocommit('localsettings')}}
