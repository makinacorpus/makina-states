{{ salt['mc_macros.register']('services', 'mail.postfix') }}
include:
  - makina-states.services.mail.postfix.hooks
  - makina-states.services.mail.postfix.prerequisites
  - makina-states.services.mail.postfix.configuration
  - makina-states.services.mail.postfix.services
