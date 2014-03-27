{% set computenode_settings = salt['mc_cloud_compute_node.settings']() %}
include:
  - makina-states.cloud.generic.hooks.common

cloud-generic-compute_node-pre-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre
    - watch_in:
      - mc_proxy: cloud-generic-pre
      - mc_proxy: cloud-generic-compute_node-post-pre-deploy

cloud-generic-compute_node-post-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-grains-deploy

cloud-generic-compute_node-pre-grains-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-grains-deploy

{% for target, vm in computenode_settings.targets.items() %}
cloud-{{target}}-generic-compute_node-pre-grains-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-grains-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-post-grains-deploy

cloud-{{target}}-generic-compute_node-post-grains-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-grains-deploy
{% endfor %}

cloud-generic-compute_node-post-grains-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-hostsfiles-deploy

cloud-generic-compute_node-pre-hostsfiles-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-hostsfiles-deploy

{% for target, vm in computenode_settings.targets.items() %}
cloud-{{target}}-generic-compute_node-pre-hostsfiles-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-hostsfiles-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-post-hostsfiles-deploy

cloud-{{target}}-generic-compute_node-post-hostsfiles-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-hostsfiles-deploy
{% endfor %}

cloud-generic-compute_node-post-hostsfiles-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-host-ssh-key-deploy

cloud-generic-compute_node-pre-host-ssh-key-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-host-ssh-key-deploy

{% for target, vm in computenode_settings.targets.items() %}
cloud-{{target}}-generic-compute_node-pre-host-ssh-key-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-host-ssh-key-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-post-host-ssh-key-deploy

cloud-{{target}}-generic-compute_node-post-host-ssh-key-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-host-ssh-key-deploy
{% endfor %}

cloud-generic-compute_node-post-host-ssh-key-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-deploy

cloud-generic-compute_node-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-firewall-deploy

cloud-generic-compute_node-pre-firewall-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-firewall-deploy

{% for target, vm in computenode_settings.targets.items() %}
cloud-{{target}}-generic-compute_node-pre-firewall-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-firewall-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-post-firewall-deploy

cloud-{{target}}-generic-compute_node-post-firewall-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-firewall-deploy
{% endfor %}

cloud-generic-compute_node-post-firewall-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-reverseproxy-deploy

cloud-generic-compute_node-pre-reverseproxy-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-reverseproxy-deploy

{% for target, vm in computenode_settings.targets.items() %}
cloud-{{target}}-generic-compute_node-pre-reverseproxy-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-reverseproxy-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-post-reverseproxy-deploy

cloud-{{target}}-generic-compute_node-post-reverseproxy-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-reverseproxy-deploy
{% endfor %}

cloud-generic-compute_node-post-reverseproxy-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-virt-type-deploy

cloud-generic-compute_node-pre-virt-type-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-virt-type-deploy

{% for target, vm in computenode_settings.targets.items() %}
cloud-{{target}}-generic-compute_node-pre-virt-type-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-virt-type-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-post-virt-type-deploy

cloud-{{target}}-generic-compute_node-post-virt-type-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-virt-type-deploy
{% endfor %}

cloud-generic-compute_node-post-virt-type-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-images-deploy

cloud-generic-compute_node-pre-images-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-images-deploy

{% for target, vm in computenode_settings.targets.items() %}
cloud-{{target}}-generic-compute_node-pre-images-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-images-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-post-images-deploy

cloud-{{target}}-generic-compute_node-post-images-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-images-deploy
{% endfor %}

cloud-generic-compute_node-post-images-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-deploy

cloud-generic-compute_node-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-post-deploy

cloud-generic-compute_node-pre-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-post-deploy

cloud-generic-compute_node-post-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-final

cloud-generic-compute_node-final:
  mc_proxy.hook:
   - watch_in:
      - mc_proxy: cloud-generic-final

