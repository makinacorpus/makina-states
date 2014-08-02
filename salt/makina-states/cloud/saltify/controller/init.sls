{% set cloudSettings= salt['mc_cloud.settings']() %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}

include:
  - makina-states.cloud.saltify.controller.hooks

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

profiles_saltify_salt:
  file.managed:
    - template: jinja
    - source: salt://makina-states/files/etc/salt/cloud.profiles.d/makinastates_saltify.conf
    - name: {{pfdir}}/makinastates_saltify.conf
    - user: root
    - group: root
    - makedirs: true
    - require:
      - mc_proxy: cloud-saltify-pre-pre-deploy
    - require_in:
      - mc_proxy: cloud-saltify-post-pre-deploy

