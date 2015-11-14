{% import "makina-states/_macros/h.jinja" as h with context %}
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{%- set locs = salt['mc_locations.settings']() %}
{% set pkgs = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_virtualbox.settings']() %}
include:
  - makina-states.services.virt.virtualbox.hooks

{% macro orch_before() %}
    - watch:
      - mc_proxy: ms-desktoptools-pkgm-pre
{% endmacro %}
{% macro orch_after() %}
    - watch_in:
      - mc_proxy: ms-desktoptools-pkgm-post
{% endmacro %}
{{h.repomanaged('deb http://download.virtualbox.org/virtualbox/debian {0} contrib'.format(pkgs.dist),
                '/etc/apt/sources.list.d/vbox.list',
                before_macro=orch_before,
                after_macro=orch_after,
                suf='virtualbox',
                key_url='https://www.virtualbox.org/download/oracle_vbox.asc')}}

virtualbox-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - pkgrepo: repomanaged-virtualbox
      - mc_proxy: virtualbox-pre-install
    - watch_in:
      - mc_proxy: virtualbox-post-install
    - pkgs: {{settings.packages}}
{% endif %}
