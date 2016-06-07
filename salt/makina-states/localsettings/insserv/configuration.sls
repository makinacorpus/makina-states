{%- import "makina-states/_macros/h.jinja" as h with context %}
{%- set settings=salt['mc_insserv.settings']() %}
include:
  - makina-states.localsettings.sshkeys.hooks
{% macro rmacro() %}
    - watch:
      - mc_proxy: localsettings-inssserv-pre
    - watch_in:
      - mc_proxy: localsettings-inssserv-post
{% endmacro %}
{{- h.deliver_config_files(
     settings.get('configs', {}),
     mode='644',
     after_macro=rmacro, prefix='inssserv-')}}
