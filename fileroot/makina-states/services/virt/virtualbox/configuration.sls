{% import "makina-states/_macros/h.jinja" as h with context %}
{% set settings = salt['mc_virtualbox.settings']() %}
include:
  - makina-states.services.virt.virtualbox.hooks
  - makina-states.services.virt.virtualbox.services
{% macro rmacro() %}
    - watch:
      - mc_proxy: virtualbox-pre-install
    - watch_in:
      - mc_proxy: virtualbox-post-install
{% endmacro %}
{{ h.deliver_config_files(settings.get('extra_confs', {}), after_macro=rmacro, prefix='vb-conf-')}}
