{%- set nt_reg = salt['mc_nodetypes.registry']() %}
{{ salt['mc_macros.register']('services', 'virt.lxc') }}
include:
  - makina-states.services.virt.lxc.prerequisites
  - makina-states.services.virt.lxc.configuration
  - makina-states.services.virt.lxc.hooks
{% if nt_reg['is']['devhost'] %}
  - makina-states.services.virt.lxc.devhost
{% endif %}
