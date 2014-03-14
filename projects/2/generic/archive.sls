{% set cfg = opts['ms_project'] %}
{% macro do() %}
{% set dest = '{0}/project'.format(cfg['current_archive_dir']) %}
{{cfg.name}}-sav-project-dir:
  cmd.run:
    - name: |
            if [ ! -d "{{dest}}" ];then
              mkdir -p "{{dest}}";
            fi;
            rsync -Aav --delete "{{cfg.project_root}}/" "{{dest}}/"
    - user: {{cfg.user}}
{% endmacro %}
{{do()}}
