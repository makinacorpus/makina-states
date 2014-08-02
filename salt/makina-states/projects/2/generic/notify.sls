{% set cfg = opts['ms_project'] %}
{% set f= '{0}/project.failed'.format(cfg['current_archive_dir']) %}
notification:
  cmd.run:
    - name: |
            {% if cfg['rollback'] %}
            echo "Project {{cfg.name}} has been rollbacked due to error (failed deploy in {{f}})"
            {% else %}
            echo "Project {{cfg.name}} has been deployed !"
            {%endif %}

