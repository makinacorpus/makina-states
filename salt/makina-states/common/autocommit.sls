{% set locations = salt['mc_locations.settings']()%}
{# be sure to run at the end of provisionning to commit
{# be sure to run at the end of provisionning to commit
# /etc changes #}
final-etckeeper-run:
  cmd.run:
    - order: last
    - name: {{locations.conf_dir}}/cron.daily/etckeeper "commit from salt"
    - onlyif: >
        test -e {{locations.conf_dir}}/cron.daily/etckeeper
        &&
        test -e $(which etckeeper 2>/dev/null)
