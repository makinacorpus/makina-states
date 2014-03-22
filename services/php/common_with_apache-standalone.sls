{#- Install in full mode, see the standalone file ! #}
{% import  "makina-states/services/php/common-standalone.sls" as base with context %}
{% set includes = base.includes %}
{% set common_includes= base.common_includes %}
{% set do = base.do %}
{% set full = False %}
{% set apache = True %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set nodetypes_registry = salt['mc_nodetypes.registry']() %}
{% set locs = base.locs %}
{% set phpSettings = salt['mc_php.settings']() %}

include:
{{ base.includes(full=full, apache=apache) }}
{{ base.do(full=full, apache=apache) }}
