include:
  - makina-states.cloud.generic.hooks.compute_node
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
{% set csettings = salt['mc_cloud.settings']() %}
{% set settings = salt['mc_cloud_compute_node.settings']() %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% for target, data in settings['targets'].iteritems() %}
{% set cptslsname = '{1}/{0}/reverseproxy'.format(target.replace('.', ''),
                                                  csettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
# get an haproxy proxying all request on 80+43 + alternate ports for ssh traffic
{% set sdata = data|yaml %}
{% set sdata = sdata.replace('\n', ' ') %}
{{target}}-gen-haproxy-installation:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - contents: |
              include:
                - makina-states.services.proxy.haproxy
              cpt-cloud-target{{target}}-haproxy-cfg:
                file.managed:
                  - name: {{salt['mc_haproxy.settings']().config_dir}}/extra/cloudcontroller.cfg
                  - source: salt://makina-states/files/etc/haproxy/cloudcontroller.cfg
                  - user: root
                  - group: root
                  - mode: 644
                  - makedirs: true
                  - template: jinja
                  - defaults:
                    cdata: {{sdata}}
                  - watch_in:
                    - mc_proxy.hook: haproxy-post-conf-hook
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-reverseproxy-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-reverseproxy-deploy
{% endfor %} 
