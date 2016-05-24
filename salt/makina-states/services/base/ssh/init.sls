# see also users.sls
{{ salt['mc_macros.register']('services', 'base.ssh') }}
include:
  - makina-states.services.base.ssh.hooks
  - makina-states.services.base.ssh.rootkey
  - makina-states.services.base.ssh.client
  - makina-states.localsettings.sshkeys
  - makina-states.services.base.ssh.server
