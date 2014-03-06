{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings= services.cloudSettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{% set localsettings = services.localsettings %}
{% macro do(full=False) %}
{{- salt["mc_macros.register"]("services", "cloud.saltify") }}
include:
  - makina-states.services.cloud.saltify-hooks
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
    - defaults:
      data: {{cloudSettings|yaml}}
      msr: {{saltmac.msr}}

profiles_saltify_salt:
  file.managed:
    - template: jinja
    - source: salt://makina-states/files/etc/salt/cloud.profiles.d/makinastates_saltify.conf
    - name: {{pfdir}}/makinastates_saltify.conf
    - user: root
    - group: root
    - defaults:
      data: {{cloudSettings|yaml}}
      msr: {{saltmac.msr}}
    - require:
      - mc_proxy: salt-cloud-postinstall
    - require_in:
      - mc_proxy: salt-cloud-predeploy
      - mc_proxy: saltify-pre-install

{% for target, data in cloudSettings.salty_targets.items() %}
{%    set name = data['name'] %}
{{target}}-{{name}}-saltify-deploy:
  cloud.profile:
    - require:
      - mc_proxy: salt-cloud-predeploy
    - require_in:
      - mc_proxy: saltify-post-install
      - mc_proxy: salt-cloud-postdeploy
    - unless: test -e {{cloudSettings.prefix}}/pki/master/minions/{{name}}
    - name: {{name}}
    - minion: {master: "{{data.master}}",
               master_port: {{data.master_port}}}
    - profile: {{data.profile}}
{%    for var in ["ssh_username",
                  "password",
                  "script_args",
                  "ssh_host",
                  "sudo_password",
                  "sudo"] %}
{%      if data.get(var) %}
    - {{var}}: {{data[var]}}
{%      endif%}
{%    endfor%}
{% endfor %}
{% endmacro %}
{{do(full=False)}}
