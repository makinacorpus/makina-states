{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{# see makina-states.controllers.standalone #}
include:
  - makina-states.controllers.standalone

{# be sure to run at the end of provisionning to commit
 # /etc changes #}
{{localsettings.autocommit('controllers')}}
