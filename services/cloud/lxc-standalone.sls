{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{% set localsettings = services.localsettings %}
{% macro do(full=False) %}
{{- salt["mc_macros.register"]("services", "cloud.lxc") }}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.services.virt.lxc-hooks
{% if full %}
  - makina-states.services.cloud.salt_cloud
{% else %}
  - makina-states.services.cloud.salt_cloud-hooks
  - makina-states.services.cloud.salt_cloud-standalone
{% endif %}

providers_lxc_salt:
  file.managed:
    - require:
      - mc_proxy: salt-cloud-postinstall
    - require_in:
      - mc_proxy: salt-cloud-predeploy
    - source: salt://makina-states/files/etc/salt/cloud.providers.d/makinastates_lxc.conf
    - name: {{pvdir}}/makinastates_lxc.conf
    - user: root
    - template: jinja
    - group: root
    - defaults:
        data: {{lxcSettings|yaml}}
        cdata: {{cloudSettings|yaml}}
        msr: {{saltmac.msr}}

profiles_lxc_salt:
  file.managed:
    - template: jinja
    - source: salt://makina-states/files/etc/salt/cloud.profiles.d/makinastates_lxc.conf
    - name: {{pfdir}}/makinastates_lxc.conf
    - user: root
    - group: root
    - defaults:
        cdata: {{cloudSettings|yaml}}
        data: {{lxcSettings|yaml}}
        msr: {{saltmac.msr}}
    - require:
      - mc_proxy: salt-cloud-postinstall
    - require_in:
      - mc_proxy: salt-cloud-predeploy


{% for target, containers in services.lxcSettings.containers.items() %}
{%  for k, data in containers.items() -%}
{%    set name = k %}
{%    set dnsservers = lxc_data.get("dnsservers") -%}
{{target}}-{{k}}-lxc-deploy:
  cloud.profile:
    - require:
      - mc_proxy: lxc-post-inst
      - mc_proxy: salt-cloud-predeploy
    - require_in:
      - mc_proxy: salt-cloud-postdeploy
    - name: {{name}}
    - cloud_provider: {{target}}
    - profile: {{data.profile}}
{%    for var in ["from_container",
                   "snapshot",
                   "image",
                   "gateway",
                   "bridge",
                   "mac",
                   "ip4",
                   "netmask",
                   "size",
                   "backing",
                   "vgname",
                   "lvname",
                   "dnsserver",
                   "ssh_username",
                   "ssh_password",
                   "lxc_conf",
                   "lxc_conf_unset"] %}
{%      if data.get(var) %}
    - {{var}}: {{lxc_data[var]}}
{%      endif%}
{%    endfor%}
{%  endfor %}
{% endfor %}
{% endmacro %}
{{do(full=False)}}
