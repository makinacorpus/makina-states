{% set data = salt['mc_tomcat.settings']() %}
{% set ver = data.ver %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set locs = salt['mc_locations.settings']() %}
{% set conf_dir = data.conf_dir %}

{{ salt['mc_macros.register']('services', 'java.tomcat7') }}
include:
  - makina-states.services.java.tomcat.hooks
  - makina-states.localsettings.jdk
  - makina-states.localsettings.jdk-hooks
  - makina-states.services.java.tomcat.prerequisites
  - makina-states.services.java.tomcat.configuration
  - makina-states.services.java.tomcat.service

