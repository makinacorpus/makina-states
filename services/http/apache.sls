{#- Install in full mode, see the standalone file ! #}
{% import "makina-states/services/http/apache-standalone.sls" as base with context %}
{% set localsettings = base.localsettings %}
{% set apacheSettings = salt['mc_apache.settings']() %} %}
{% set extend_switch_mpm = base.extend_switch_mpm %}
{{ base.do(full=True) }}
