# see also users.sls
{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set locs = salt['mc_localsettings.settings']()['locations'] %}
{% set openssh = salt['mc_ssh.settings']() %}

{{ salt['mc_macros.register']('services', 'base.ssh') }}
include:
  - makina-states.localsettings.users
  - makina-states.services.base.ssh.hooks
  - makina-states.services.base.ssh.client
  - makina-states.services.base.ssh.server
  - makina-states.services.base.ssh.rootkey

