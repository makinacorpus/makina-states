{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set computenodeSettings = salt['mc_cloud_compute_node.settings']() %}
include:
  - makina-states.cloud.generic.hooks.compute_node
  - makina-states.cloud.generic.genssh
{% for target, vm in computenodeSettings.targets.items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set cptslsname = '{1}/{0}/compute_node_sshkeyinstall'.format(target.replace('.', ''),
                                                           csettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
{{target}}-inst-lxc-host-install-ssh-key:
  file.managed:
    - name: {{cptsls}}
    - watch:
      - file: {{target}}-lxc-root-keygen
    - user: root
    - mode: 750
    - makedirs: true
    - contents: |
                inskey:
                  ssh_auth.present:
                    - source: salt://rootpubkey.pub
                    - user: root
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-host-ssh-key-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-host-ssh-key-deploy
{% endfor %}
