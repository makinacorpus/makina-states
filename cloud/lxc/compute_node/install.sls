include:
  - makina-states.cloud.lxc.compute_node.pre-deploy.install
  - makina-states.cloud.lxc.compute_node.deploy.install
  - makina-states.cloud.lxc.compute_node.post-deploy.install
{% if salt['mc_nodetypes.registry']().is.devhost %}
  - makina-states.cloud.lxc.compute_node.devhost.install
{% endif %}
