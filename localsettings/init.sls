{%- import "makina-states/_macros/funcs.jinja" as funcs with context %}
{# see makina-states.localsettings.standalone #}
include:
  - makina-states.localsettings.standalone

{# POST INSTALLATION ORCHESTRATION STUFF #}
{{funcs.autocommit('localsettings')}}
