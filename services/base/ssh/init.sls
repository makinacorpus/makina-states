# see also users.sls
{{ salt['mc_macros.register']('services', 'base.ssh') }}
include:
  - makina-states.services.base.ssh.hooks
  - makina-states.services.base.ssh.rootkey
  - makina-states.services.base.ssh.client
{% if salt['mc_nodetypes.activate_sysadmin_states']() %}
  - makina-states.localsettings.users
  - makina-states.services.base.ssh.server
{% endif %}
