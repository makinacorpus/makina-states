{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set computenode_settings = salt['mc_cloud_compute_node.settings']() %}

include:
  - makina-states.cloud.generic.hooks.common

cloud-generic-vm-pre-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-pre-deploy

{% for target, tdata in computenode_settings.targets.items() %}
{% for vmname, vmdata in tdata.vms.items() %}
cloud-{{vmname}}-generic-vm-pre-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-pre-pre-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-pre-deploy

cloud-{{vmname}}-generic-vm-post-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-pre-deploy
{% endfor %}
{% endfor %}

cloud-generic-vm-post-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-deploy

cloud-generic-vm-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-deploy

{% for target, tdata in computenode_settings.targets.items() %}
{% for vmname, vmdata in tdata.vms.items() %}
cloud-{{vmname}}-generic-vm-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-pre-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-deploy

cloud-{{vmname}}-generic-vm-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-deploy
{% endfor %}
{% endfor %}

cloud-generic-vm-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-post-deploy

cloud-generic-vm-pre-install-ssh-key:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-install-ssh-key

{% for target, tdata in computenode_settings.targets.items() %}
{% for vmname, vmdata in tdata.vms.items() %}
cloud-{{vmname}}-generic-vm-pre-install-ssh-key:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
      - mc_proxy: cloud-generic-vm-pre-install-ssh-key
    - watch_in:
      - mc_proxy:  cloud-{{vmname}}-generic-vm-post-install-ssh-key

cloud-{{vmname}}-generic-vm-post-install-ssh-key:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-install-ssh-key
{% endfor %}
{% endfor %}

cloud-generic-vm-post-install-ssh-key:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-hostsfiles-deploy

cloud-generic-vm-pre-hostsfiles-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-hostsfiles-deploy

{% for target, tdata in computenode_settings.targets.items() %}
{% for vmname, vmdata in tdata.vms.items() %}
cloud-{{vmname}}-generic-vm-pre-hostsfiles-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-pre-hostsfiles-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-hostsfiles-deploy

cloud-{{vmname}}-generic-vm-post-hostsfiles-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-hostsfiles-deploy
{% endfor %}
{% endfor %}

cloud-generic-vm-post-hostsfiles-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-initial-highstate-deploy

cloud-generic-vm-pre-initial-setup-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-initial-setup-deploy

{% for target, tdata in computenode_settings.targets.items() %}
{% for vmname, vmdata in tdata.vms.items() %}
cloud-{{vmname}}-generic-vm-pre-initial-setup-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
      - mc_proxy: cloud-generic-vm-pre-initial-setup-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-initial-setup-deploy

cloud-{{vmname}}-generic-vm-post-initial-setup-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-initial-setup-deploy
{% endfor %}
{% endfor %}

cloud-generic-vm-post-initial-setup-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
      - mc_proxy: cloud-generic-vm-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-grains-deploy

cloud-generic-vm-pre-grains-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-grains-deploy

{% for target, tdata in computenode_settings.targets.items() %}
{% for vmname, vmdata in tdata.vms.items() %}
cloud-{{vmname}}-generic-vm-pre-grains-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
      - mc_proxy: cloud-generic-vm-pre-grains-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-grains-deploy

cloud-{{vmname}}-generic-vm-post-grains-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-grains-deploy

{% endfor %}
{% endfor %}

cloud-generic-vm-post-grains-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-initial-setup-deploy
      - mc_proxy: cloud-generic-vm-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-initial-highstate-deploy


cloud-generic-vm-pre-initial-highstate-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-initial-highstate-deploy

{% for target, tdata in computenode_settings.targets.items() %}
{% for vmname, vmdata in tdata.vms.items() %}
cloud-{{vmname}}-generic-vm-pre-initial-highstate-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
      - mc_proxy: cloud-generic-vm-post-initial-setup-deploy
      - mc_proxy: cloud-generic-vm-pre-initial-highstate-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-initial-highstate-deploy

cloud-{{vmname}}-generic-vm-post-initial-highstate-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-initial-highstate-deploy
{% endfor %}
{% endfor %}

cloud-generic-vm-post-initial-highstate-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
      - mc_proxy: cloud-generic-vm-post-initial-setup-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-post-deploy

cloud-generic-vm-pre-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-post-deploy

{% for target, tdata in computenode_settings.targets.items() %}
{% for vmname, vmdata in tdata.vms.items() %}
cloud-{{vmname}}-generic-vm-pre-post-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-deploy
      - mc_proxy: cloud-generic-vm-post-initial-setup-deploy
      - mc_proxy: cloud-generic-vm-post-initial-highstate-deploy
      - mc_proxy: cloud-generic-vm-pre-post-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-post-deploy

cloud-{{vmname}}-generic-vm-post-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-post-deploy
{% endfor %}
{% endfor %}

cloud-generic-vm-post-post-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-initial-setup-deploy
      - mc_proxy: cloud-generic-vm-post-initial-highstate-deploy
      - mc_proxy: cloud-generic-vm-pre-post-deploy
      - mc_proxy: cloud-generic-vm-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-final

cloud-generic-vm-final:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-final
