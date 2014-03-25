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
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{% set cptslsname = '{1}/{0}/compute_node_reverseproxy'.format(target.replace('.', ''),
                                                  cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{% set sdata = data|yaml %}
{% set sdata = sdata.replace('\n', ' ') %}
# get an haproxy proxying all request on 80+43 + alternate ports for ssh traffic
{{target}}-gen-haproxy-installation:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - contents: |
              {% raw %}{%set sdata = "{% endraw %}{{sdata.replace('\n', ' ')}}{% raw %}" %}{% endraw %}
              include:
                - makina-states.services.proxy.haproxy
              cpt-cloud-target{{target}}-haproxy-cfg:
                file.managed:
                  - name: {%raw%}{{salt['mc_haproxy.settings']().config_dir}}{%endraw%}/extra/cloudcontroller.cfg
                  - source: salt://makina-states/files/etc/haproxy/cloudcontroller.cfg
                  - user: root
                  - group: root
                  - mode: 644
                  - makedirs: true
                  - template: jinja
                  - defaults:
                    cdata: {%raw%}"{{sdata}}"{%endraw%}
                  - watch_in:
                    - mc_proxy.hook: haproxy-post-conf-hook
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-reverseproxy-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-reverseproxy-deploy
{% endfor %} 
