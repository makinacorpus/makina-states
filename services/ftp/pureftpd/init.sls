{{ salt['mc_macros.register']('services', 'ftp.pureftpd') }}
include:
  - makina-states.services.ftp.pureftpd.prerequisites
  - makina-states.services.ftp.pureftpd.configuration
  - makina-states.services.ftp.pureftpd.services
