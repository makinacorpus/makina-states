include:
  - makina-states.cloud.generic.hooks.compute_node
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set csettings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in csettings['targets'].items() %}
{% if data.virt_types.lxc %}
{% set cptslsname = '{1}/{0}/lxc/installation'.format(target.replace('.', ''),
                                                 cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{{target}}-gen-lxc-images-templates:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-virt-type-deploy
    - watch_in:
      - mc_proxy: cloud-{{name}}-generic-compute_node-pre-virt-type-deploy
    - contents: |
      {% raw %}
      {% set lxcSettings = salt['mc_lxc.settings']() %}
      include:
          - makina-states.cloud.lxc.hooks
          - makina-states.services.firewall.shorewall
          - makina-states.services.virt.lxc
        {% if grains['os'] not in ['Ubuntu'] %}
        etc-init.d-lxc-net-makina:
          file.managed:
            - name: /etc/init.d/lxc-net-makina
            - template: jinja
            - defaults: {{lxcSettings.defaults|yaml}}
            - source: salt://makina-states/files/etc/init.d/lxc-net-makina.sh
            - mode: 750
            - user: root
            - group: root
            - require_in:
              - service: lxc-services-enabling
        {% else %}
        etc-init-lxc-net-makina:
          file.managed:
            - name: /etc/init/lxc-net-makina.conf
            - template: jinja
            - source: salt://makina-states/files/etc/init/lxc-net-makina.conf
            - mode: 750
            - user: root
            - defaults: {{lxcSettings.defaults|yaml}}
            - group: root
            - require_in:
              - service: lxc-services-enabling
        {% endif %}
        lxc-makina-services-enabling:
          service.running:
            - enable: True
            - names:
              - lxc
              - lxc-net
              - lxc-net-makina
            - require_in:
              - mc_proxy: lxc-post-inst
        {% endraw %}
{% endif %}
{% endfor %}
maybe-only-one-gen-lxc:
  mc_proxy.hook : []

