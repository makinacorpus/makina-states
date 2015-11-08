{{ salt['mc_macros.register']('services', 'mail.dovecot') }}
include:
  - makina-states.services.mail.dovecot.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services.mail.dovecot.prerequisites
  - makina-states.services.mail.dovecot.configuration
  - makina-states.services.mail.dovecot.services
{% endif %}
