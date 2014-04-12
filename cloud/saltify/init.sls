{{- salt["mc_macros.register"]("cloud", "saltify") }}
{% set cloudSettings= salt['mc_cloud.settings']() %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}

include:
  - makina-states.cloud.saltify.hooks

providers_saltify_salt:
  file.managed:
    - require:
      - mc_proxy: cloud-saltify-pre-pre-deploy
    - require_in:
      - mc_proxy: cloud-saltify-post-pre-deploy
    - source: salt://makina-states/files/etc/salt/cloud.providers.d/makinastates_saltify.conf
    - name: {{pvdir}}/makinastates_saltify.conf
    - user: root
    - template: jinja
    - makedirs: true
    - group: root
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](cloudSettings)}}
      msr: {{cloudSettings.root}}/makina-states

profiles_saltify_salt:
  file.managed:
    - template: jinja
    - source: salt://makina-states/files/etc/salt/cloud.profiles.d/makinastates_saltify.conf
    - name: {{pfdir}}/makinastates_saltify.conf
    - user: root
    - group: root
    - makedirs: true
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](cloudSettings)}}
      msr: {{cloudSettings.root}}/makina-states
    - require:
      - mc_proxy: cloud-saltify-pre-pre-deploy
    - require_in:
      - mc_proxy: cloud-saltify-post-pre-deploy

