{{- salt['mc_macros.register']('services', 'monitoring.icinga_cgi') }}
include:
#   icinga-cgi depends on icinga unless files are accessed through network (sshfs, nfs, ...)
#   in ubuntu, icinga-cgi package depends on icinga-common
  - makina-states.services.monitoring.icinga
  - makina-states.services.monitoring.icinga_cgi.nginx
  - makina-states.services.monitoring.icinga_cgi.prerequisites
  - makina-states.services.monitoring.icinga_cgi.configuration
  - makina-states.services.monitoring.icinga_cgi.services
