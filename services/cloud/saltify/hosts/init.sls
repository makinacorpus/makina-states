{% import "makina-states/_macros/services.jinja" as services with context %}
{% set cloudSettings= services.cloudSettings %}
include:
  - makina-states.services.cloud.saltify.hooks

{% for target, data in cloudSettings.salty_targets.items() %}
{%    set name = data['name'] %}
{{target}}-{{name}}-saltify-deploy:
  cloud.profile:
    - require:
      - mc_proxy: saltify-pre-deploy
    - require_in:
      - mc_proxy: saltify-post-deploy
    - unless: test -e {{cloudSettings.prefix}}/pki/master/minions/{{name}}
    - name: {{name}}
    - minion: {master: "{{data.master}}",
               master_port: {{data.master_port}}}
    - profile: {{data.profile}}
{%    for var in ["ssh_username",
                  "keep_tmp",
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
