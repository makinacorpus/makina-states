include:
  - makina-states.cloud.generic.hooks.compute_node
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{% set cptslsname = '{1}/{0}/compute_node_grains'.format(target.replace('.', ''),
                                                   cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{{target}}-gen-grains-installation:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - contents: |
        {{target}}-run-grains:
          grains.present:
            - names:
              - makina-states.cloud.is.compute_node
              - makina-states.services.proxy.haproxy
              - makina-states.services.firewall.shorewall
              - makina-states.cloud.compute_node.has.firewall
            - value: true
        {{ target }}-reload-grains:
          cmd.script:
            - source: salt://makina-states/_scripts/reload_grains.sh
            - template: jinja
            - watch:
              - cmd: {{target}}-run-grains
    - watch:
      - mc_proxy: cloud-generic-compute_node-post-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-grains-deploy
{% endfor %}
