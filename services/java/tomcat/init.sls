{{ salt['mc_macros.register']('services', 'java.tomcat') }}
include:
  - makina-states.services.java.tomcat.hooks
  - makina-states.localsettings.jdk
  - makina-states.localsettings.jdk.hooks
  - makina-states.services.java.tomcat.prerequisites
  - makina-states.services.java.tomcat.configuration
  - makina-states.services.java.tomcat.services
