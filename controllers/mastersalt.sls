{#- Install in full mode, see the standalone file !  #}
{% import  "makina-states/controllers/mastersalt-standalone.sls" as base with context %}
{% set controllers = base.controllers %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set saltmac = base.saltmac %}
{% set name = base.name %}
{{base.do(full=True)}}
