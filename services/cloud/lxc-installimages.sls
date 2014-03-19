{% import "makina-states/_macros/services.jinja" as services with context %}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.services.virt.lxc-hooks
  - makina-states.services.cloud.salt_cloud-hooks
  - makina-states.services.cloud.lxc-hooks
{% for target in services.lxcSettings.containers %}
{{target}}-lxc-images-install:
  salt.state:
    - tgt: [{{grains['id']}}]
    - expr_form: list
    - sls: makina-states.services.cloud.lxc-images
    - concurrent: True
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template
{%endfor%}
{% if not grains['id'] in services.lxcSettings['containers'] %}
{{grains['id']}}-lxc-images-controller-install:
  salt.state:
    - tgt: [{{grains['id']}}]
    - expr_form: list
    - concurrent: True
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template
{% endif %}
{% if services.lxcSettings['cron_sync'] %}
syncron-lxc-ms:
  cron.present:
    - minute: {{services.lxcSettings.cron_minute}}
    - hour: {{services.lxcSettings.cron_hour}}
    - name: /usr/bin/mastersalt-run -linfo mc_lxc.sync_images > /dev/null
    - identifier: ms lxc image synchronniser
{% endif %}
