{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings= services.cloudSettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{% set localsettings = salt['mc_localsettings.settings']() %}

include:
- makina-states.services.cloud.saltify.hooks

providers_saltify_salt:
  file.managed:
    - require:
      - mc_proxy: saltify-pre-install
    - require_in:
      - mc_proxy: saltify-post-install
    - source: salt://makina-states/files/etc/salt/cloud.providers.d/makinastates_saltify.conf
    - name: {{pvdir}}/makinastates_saltify.conf
    - user: root
    - template: jinja
    - makedirs: true
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
    - makedirs: true
    - defaults:
      data: {{cloudSettings|yaml}}
      msr: {{saltmac.msr}}
    - require:
      - mc_proxy: saltify-pre-install
    - require_in:
      - mc_proxy: saltify-post-install

