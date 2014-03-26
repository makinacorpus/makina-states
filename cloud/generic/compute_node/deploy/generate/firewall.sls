include:
  - makina-states.cloud.generic.hooks.compute_node
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{% set cptslsname = '{1}/{0}/compute_node_firewall'.format(target.replace('.', ''),
                                                  cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{% set rcptslsname = '{1}/{0}/run-compute_node_firewall'.format(target.replace('.', ''),
                                                      cloudSettings.compute_node_sls_dir) %}
{% set rcptsls = '{1}/{0}.sls'.format(rcptslsname, cloudSettings.root) %}
# get an haproxy proxying all request on 80+43 + alternate ports for ssh traffic
{{target}}-gen-firewall-installation:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - contents: |
              include:
                - makina-states.services.firewall.shorewall
              cloud-{{target}}-hook:
                mc_proxy.hook: []
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-firewall-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-pre-firewall-deploy
{{target}}-gen-firewall-installation-run:
  file.managed:
    - name: {{rcptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-firewall-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-pre-firewall-deploy
    - contents: |
            include:
              - makina-states.cloud.generic.hooks.compute_node
            {{target}}-run-firewall-installation:
              salt.state:
                - tgt: [{{target}}]
                - expr_form: list
                - sls: {{cptslsname.replace('/', '.')}}
                - concurrent: True
                - watch:
                  - mc_proxy: cloud-{{target}}-generic-compute_node-pre-firewall-deploy
                - watch_in:
                  - mc_proxy: cloud-{{target}}-generic-compute_node-post-firewall-deploy
{% endfor %}
