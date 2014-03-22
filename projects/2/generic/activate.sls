{% import "makina-states/_macros/services.jinja" as services with context %}
{# export macro to callees #}
{% set services = services %}
{% set nodetypes = services.nodetypes %}
{% set localsettings = services.localsettings %}
{% set locs = salt['mc_localsettings']()['locations'] %}

{% set cfg = opts['ms_project'] %}
{% macro do() %}
{%- if not cfg.no_reset_perms %}
{{cfg.name}}-restricted-perms:
  file.managed:
    - name: {{cfg.project_dir}}/global-reset-perms.sh
    - mode: 750
    - user: {% if not cfg.no_user%}{{cfg.user}}{% else -%}root{% endif %}
    - group: {{cfg.group}}
    - contents: >
            #!/usr/bin/env bash

            if [ -e "{{cfg.pillar_root}}" ];then
            "{{locs.resetperms}}" "${@}"
            --dmode '0770' --fmode '0770'
            --user root --group "{{localsettings.group}}"
            --users root
            --groups "{{localsettings.group}}"
            --paths "{{cfg.pillar_root}}";fi

            if [ -e "{{cfg.project_root}}" ];then
            "{{locs.resetperms}}" "${@}"
            --dmode '0770' --fmode '0770'
            --paths "{{cfg.project_root}}"
            --users {% if not cfg.no_user%}{{cfg.user}}{% else -%}root{% endif %}
            --groups {{cfg.group}}
            --user {% if not cfg.no_user%}{{cfg.user}}{% else -%}root{% endif %}
            --group {{cfg.group}};fi

{{cfg.name}}-perms:
  cmd.run:
    - name: {{cfg.project_dir}}/global-reset-perms.sh
    - cwd: {{cfg.project_root}}
    - user: root
    - watch:
      - file: {{cfg.name}}-restricted-perms
{% endif %}
{% endmacro %}
{{do()}}
