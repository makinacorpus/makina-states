include:
  - makina-states.cloud.generic.hooks
{# to reverse proxy a host, by default we redirect only and only:
 #  - http
 #  - https
 #  - ssh
 #
 # we can reverse proxy http & https but not ssh
 # for ssh, we are on a /16 by default (10.5/16)
 # so we have 256*254 maximum ports to redirect
 # We start by default at 40000   e
 # eg ip: 10.5.0.1 will have its ssh port mapped to 40001 on host
 # eg ip: 10.5.0.2 will have its ssh port mapped to 40002 on host
 # eg ip: 10.5.1.2 will have its ssh port mapped to 40258 on host
 #}
{% set csettings = salt['mc_cloud_controller.settings']() %}
{% set settings = salt['mc_cloud_compute_node.settings']() %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% for target, data in settings['reverse_proxies'].iteritems() %}
{% set cptslsname = '{1}/{0}/compute_node_grains'.format(target.replace('.', ''),
                                                  csettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
# get an haproxy proxying all request on 80+43 + alternate ports for ssh traffic
{% set sdata = data|yaml %}
{% set sdata = sdata.replace('\n', ' ') %}
{{target}}-run-grains-installation:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - contents: |
        {{target}}-run-grains:
          file.managed:
            - name: {{cptsls}}
              - name: makina-states.cloud.is.compute_node
              - value: true
        {{ target }}-reload-grains:
          cmd.script:
            - source: salt://makina-states/_scripts/reload_grains.sh
            - template: jinja
            - watch:
              - cmd: {{target}}-run-grains
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: {{cptslsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - file: {{target}}-run-grains-installation
    - watch_in:
      - mc_proxy: cloud-generic-pre-deploy
      - mc_proxy: cloud-generic-pre-reverseproxy-deploy
{% endfor %}
