#!/usr/bin/env bash
for i in  post_install activate reconfigure archive release_sync configure build deploy upgrade notify rollback;do
cat > $i.sls << EOF
{%raw%}{% set cfg = opts['ms_project'] %}{% endraw %}
include:
  - makina-states.projects.{% raw %}{{cfg['api_version']}}{%endraw%}.{%raw%}{{cfg['installer']}}{%endraw%}.$i
{% raw %}
{% macro do() %}
{# write your state here #}
{% endmacro %}
{{do()}}
{% endraw %}
EOF
done

