{% import "makina-states/_macros/h.jinja" as h with context %}
{% set data = salt['mc_dbus.settings']() %}
include:
  - makina-states.services.base.dbus.hooks
  - makina-states.services.base.dbus.services
{% macro rmacro() %}
    - watch:
      - mc_proxy: dbus-preconf
    - watch_in:
      - mc_proxy: dbus-postconf
{% endmacro %}
{{ h.deliver_config_files(
     data.get('extra_confs', {}), after_macro=rmacro, prefix='dbus-')}}
