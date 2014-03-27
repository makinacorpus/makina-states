include:
  - makina-states.cloud.generic.hooks.compute_node
{# to reverse proxy a host, by default we redirect only and only:
 #  - http
 #  - https
 #  - ssh
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
{% for target, tdata in compute_node_settings['targets'].items() %}
{% set cptslsname = '{1}/{0}/run-compute_node_reverseproxy'.format(target.replace('.', ''),
                                                  cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
# get an haproxy proxying all request on 80+43 + alternate ports for ssh traffic
  - {{cptslsname.replace('/', '.')}}
{% endfor %}
