{% set cfg = opts['ms_project'] %}
{% set dest = '{0}/project'.format(cfg['current_archive_dir']) %}
{% set fdest = '{0}/project.failed'.format(cfg['current_archive_dir']) %}
{{cfg.name}}-rollback-faileproject-dir:
  cmd.run:
    - name: |
            if [ -d "{{dest}}" ];then
              rsync -Aa --delete "{{cfg.project_root}}/" "{{fdest}}/"
            fi;
    - user: {{cfg.user}}

{{cfg.name}}-rollback-project-dir:
  cmd.run:
    - name: |
            if [ -d "{{dest}}" ];then
              rsync -Aa --delete "{{dest}}/" "{{cfg.project_root}}/"
            fi;
    - user: {{cfg.user}}
    - require:
      - cmd:  {{cfg.name}}-rollback-faileproject-dir
