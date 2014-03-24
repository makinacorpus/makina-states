{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set csettings = salt['mc_cloud.settings']() %}
{% set computenodeSettings = salt['mc_cloud_compute_node.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.cloud.generic.genssh
{% for target, vm in lxcSettings.vm.items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set cptslsname = '{1}/{0}/install-hosts-ssh-key'.format(target.replace('.', ''),
                                                  csettings.compute_node_sls_dir) %}
{% set saltr = csettings.root %}
{% set slspath = '{0}/{1}.sls'.format(saltr, slsname) %}
{{target}}-gen-lxc-host-install-ssh-key:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: {{slsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - file: {{target}}-lxc-host-install-ssh-key
    - watch_in:
      - mc_proxy: salt-cloud-lxc-{{target}}-ssh-key
{% endfor %}
