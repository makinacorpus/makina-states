{% import "makina-states/localsettings/sshkeys/configuration.sls" as m with context %}
{{ salt['mc_macros.register']('localsettings', 'sshkeys') }}
include:
  - makina-states.localsettings.sshkeys.configuration
  - makina-states.localsettings.sshkeys.hooks

{# retrocompat #}
{% set manage_user_ssh_keys = m.manage_user_ssh_keys %}
