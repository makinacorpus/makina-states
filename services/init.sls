{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{# see makina-states.services.standalone #}
include:
  - makina-states.services.standalone

{# be sure to run at the end of provisionning to commit
 # /etc changes #}
{{localsettings.autocommit('services')}}
