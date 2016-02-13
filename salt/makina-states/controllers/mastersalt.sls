{%- import "makina-states/_macros/salt.jinja" as saltmac with context %}

{{ salt['mc_macros.register']('controllers', 'mastersalt') }}

include:
  - makina-states.controllers.requirements
  - makina-states.controllers.hooks

{{ saltmac.install_makina_states('mastersalt') }}
