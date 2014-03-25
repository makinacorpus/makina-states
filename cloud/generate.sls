include:
  - makina-states.cloud.generic.generate
{% if salt['mc_cloud.registry']().is.lxc %}
  - makina-states.cloud.lxc.generate
{%endif %}
