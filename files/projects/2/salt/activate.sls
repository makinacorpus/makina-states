{%raw%}{% set cfg = opts['ms_project'] %}{% endraw %}
include:
  - makina-states.projects.{% raw %}{{cfg['api_version']}}{%endraw%}.{%raw%}{{cfg['installer']}}{%endraw%}.activate
{% raw %}
{% macro do() %}
{# write your state here #}
{% endmacro %}
{{do()}}
{% endraw %}
