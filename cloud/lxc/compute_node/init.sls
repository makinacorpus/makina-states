include:
  - makina-states.services.cloud.lxc.compute_node.pre-deploy
  - makina-states.services.cloud.lxc.compute_node.deploy
  - makina-states.services.cloud.lxc.compute_node.post-deploy
{% if {% salt['mc_nodetypes.registry']().is.devhost %}
  - makina-states.services.cloud.lxc.compute_node.devhost
{% endif %}
