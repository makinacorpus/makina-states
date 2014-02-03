{#- Install in full mode, see the standalone file ! #}
{% import "makina-states/services/http/apache-standalone.sls" as base with context %}
{% set nodetypes = base.nodetypes %}
{% set services = base.services %}
{% set localsettings = base.localsettings %}
{% set apacheSettings = base.apacheSettings %}
{% set extend_switch_mpm = base.extend_switch_mpm %}
{{ base.do(full=True) }}
