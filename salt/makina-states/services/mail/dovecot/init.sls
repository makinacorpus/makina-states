{{ salt['mc_macros.register']('services', 'mail.dovecot') }}
include:
  - makina-states.services.mail.dovecot.hooks
  - makina-states.services.mail.dovecot.prerequisites
  - makina-states.services.mail.dovecot.configuration
  - makina-states.services.mail.dovecot.services
