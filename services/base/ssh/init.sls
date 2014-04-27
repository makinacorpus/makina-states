# see also users.sls
{{ salt['mc_macros.register']('services', 'base.ssh') }}
include:
  - makina-states.services.base.ssh.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}  
  - makina-states.localsettings.users
  - makina-states.services.base.ssh.client
  - makina-states.services.base.ssh.server
  - makina-states.services.base.ssh.rootkey
{%endif %}
