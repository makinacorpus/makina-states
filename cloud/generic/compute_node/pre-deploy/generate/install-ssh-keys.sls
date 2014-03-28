{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
include:
  - makina-states.cloud.generic.hooks.generate
{% for target, vm in compute_node_settings.targets.items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set cptslsname = '{1}/{0}/compute_node_ssh_key'.format(target.replace('.', ''),
                                                           cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{% set rcptslsname = '{1}/{0}/run-compute_node_ssh_key'.format(target.replace('.', ''),
                                                           cloudSettings.compute_node_sls_dir) %}
{% set rcptsls = '{1}/{0}.sls'.format(rcptslsname, cloudSettings.root) %}
{{target}}-inst-lxc-host-install-ssh-key:
  file.managed:
    - name: {{cptsls}}
    - watch:
      - file: {{target}}-lxc-root-keygen
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - contents: |
                insdsakey:
                  ssh_auth.present:
                    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-dsa.pub
                    - user: root
                inskey:
                  ssh_auth.present:
                    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-rsa.pub
                    - user: root
{{target}}-gen-inst-lxc-host-install-ssh-key:
  file.managed:
    - name: {{rcptsls}}
    - watch:
      - file: {{target}}-lxc-root-keygen
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - contents : |
                 include:
                   - makina-states.cloud.generic.hooks.compute_node
                 {{target}}-gen-lxc-host-install-ssh-key:
                   salt.state:
                     - tgt: [{{target}}]
                     - expr_form: list
                     - sls: {{cptslsname.replace('/', '.')}}
                     - concurrent: True
                     - watch:
                       - mc_proxy: cloud-{{target}}-generic-compute_node-pre-host-ssh-key-deploy
                     - watch_in:
                       - mc_proxy: cloud-{{target}}-generic-compute_node-post-host-ssh-key-deploy
{% endfor %}
