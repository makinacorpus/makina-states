include:
  - makina-states.cloud.generic.install
{% if salt['mc_cloud.registry']().is.lxc %}
  - makina-states.cloud.lxc.install
{%endif %}
