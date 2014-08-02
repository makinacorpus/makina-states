{% import "makina-states/_macros/h.jinja" as h with context %}
{% set data = salt['mc_cron.settings']() %}
include:
  - makina-states.services.base.cron.hooks
  - makina-states.services.base.cron.services
{% macro rmacro() %}
    - watch:
      - mc_proxy: cron-preconf
    - watch_in:
      - mc_proxy: cron-postconf
{% endmacro %}
{{ h.deliver_config_files(
     data.get('extra_confs', {}), after_macro=rmacro, prefix='cron-')}}
