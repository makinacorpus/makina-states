{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{% set localsettings = services.localsettings %}
{% macro do(full=False) %}
{{- salt["mc_macros.register"]("services", "cloud.saltify") }}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.services.virt.saltify-hooks
{% if full %}
  - makina-states.services.cloud.salt_cloud
{% else %}
  - makina-states.services.cloud.salt_cloud-hooks
  - makina-states.services.cloud.salt_cloud-standalone
{% endif %}

providers_saltify_salt:
  file.managed:
    - require:
      - mc_proxy: salt-cloud-postinstall
    - require_in:
      - mc_proxy: salt-cloud-predeploy
      - mc_proxy: saltify-pre-install
    - source: salt://makina-states/files/etc/salt/cloud.providers.d/makinastates_saltify.conf
    - name: {{pvdir}}/makinastates_saltify.conf
    - user: root
    - template: jinja
    - group: root
    - defaults: {{lxcSettings|yaml}}

profiles_saltify_salt:
  file.managed:
    - template: jinja
    - source: salt://makina-states/files/etc/salt/cloud.profiles.d/makinastates_saltify.conf
    - name: {{pfdir}}/makinastates_saltify.conf
    - user: root
    - group: root
    - defaults: {{lxcSettings|yaml}}
    - require:
      - mc_proxy: salt-cloud-postinstall
    - require_in:
      - mc_proxy: salt-cloud-predeploy
      - mc_proxy: saltify-pre-install

{% for target, containers in services.cloudSettings.targets.items() %}
{%  for k, data in containers.items() -%}
{%    set name = k %}
{%    set dnsservers = lxc_data.get("dnsservers") -%}
{{target}}-{{k}}-saltify-deploy:
  cloud.profile:
    - require:
      - mc_proxy: lxc-post-inst
      - mc_proxy: salt-cloud-predeploy
    - require_in:
      - mc_proxy: saltify-post-install
      - mc_proxy: salt-cloud-postdeploy
    - name: {{name}}
    - cloud_provider: {{target}}
    - profile: {{data.profile}}
{%    for var in ["ssh_username",
                  "ssh_password",
                  "sudo" %}
{%      if data.get(var) %}
    - {{var}}: {{lxc_data[var]}}
{%      endif%}
{%    endfor%}
{%  endfor %}
{% endfor %}
{% endmacro %}
{{do(full=False)}}
