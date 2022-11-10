{{ salt['mc_macros.register']('services', 'monitoring.snmpd') }}
include:
  - makina-states.services.monitoring.snmpd.hooks
  - makina-states.services.monitoring.snmpd.prerequisites
  - makina-states.services.monitoring.snmpd.configuration
  - makina-states.services.monitoring.snmpd.services
