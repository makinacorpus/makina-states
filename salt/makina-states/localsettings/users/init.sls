{% import "makina-states/localsettings/users/configuration.sls" as m with context %}
{{ salt['mc_macros.register']('localsettings', 'users') }}

include:
  # too dangerous to not keep the sync state not in sync with users
  - makina-states.localsettings.sudo
  - makina-states.localsettings.shell
  - makina-states.localsettings.groups
  - makina-states.localsettings.sshkeys
  - makina-states.localsettings.users.hooks
  - makina-states.localsettings.users.configuration

{# retrocompat #}
{% set add_user = m.create_user %}
{% set create_user = m.create_user %}
