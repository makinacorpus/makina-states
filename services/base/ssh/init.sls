# see also users.sls
{{ salt['mc_macros.register']('services', 'base.ssh') }}
include:
  - makina-states.localsettings.users
  - makina-states.services.base.ssh.hooks
  - makina-states.services.base.ssh.client
  - makina-states.services.base.ssh.server
  - makina-states.services.base.ssh.rootkey

