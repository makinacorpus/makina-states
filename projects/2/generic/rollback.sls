{% set cfg = opts['ms_project'] %}
{% macro do() %}
{% set dest = '{0}/project'.format(cfg['current_archive_dir']) %}
{{cfg.name}}-rollback-project-dir:
  cmd.run:
    - name: |
            if [ -d "{{dest}}" ];then
              rsync -Aav --delete "{{dest}}/" "{{cfg.project_root}}/"
            fi;
    - user: {{cfg.user}}
{% endmacro %}
{{do()}}
