{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
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
  - makina-states.services.cloud.salt_cloud-hooks
  - makina-states.services.cloud.lxc-hooks
{% if full %}
  - makina-states.services.cloud.salt_cloud
{% else %}
  - makina-states.services.cloud.salt_cloud-standalone
{% endif %}
{% if nodetypes.registry.is.devhost %}
  - makina-states.services.cloud.lxc-devhost-sshkeys
  - makina-states.services.cloud.lxc-devhost-symlinks
  - makina-states.services.cloud.lxc-containers
  - makina-states.services.cloud.lxc-images
{% endif %}
providers_lxc_salt:
  file.managed:
    - require:
      - mc_proxy: salt-cloud-preinstall
    - require_in:
      - mc_proxy: salt-cloud-postinstall
    - source: salt://makina-states/files/etc/salt/cloud.providers.d/makinastates_lxc.conf
    - name: {{pvdir}}/makinastates_lxc.conf
    - user: root
    - template: jinja
    - group: root
    - defaults:
        data: {{lxcSettings.defaults|yaml}}
        cdata: {{cloudSettings|yaml}}
        containers: {{lxcSettings.containers.keys()|yaml }}
        msr: {{saltmac.msr}}

profiles_lxc_salt:
  file.managed:
    - template: jinja
    - source: salt://makina-states/files/etc/salt/cloud.profiles.d/makinastates_lxc.conf
    - name: {{pfdir}}/makinastates_lxc.conf
    - user: root
    - group: root
    - defaults:
        pdata: {{lxcSettings.defaults|yaml}}
        cdata: {{cloudSettings|yaml}}
        profiles: {{lxcSettings.lxc_cloud_profiles|yaml }}
        containers: {{lxcSettings.containers.keys()|yaml }}
        msr: {{saltmac.msr}}
    - require:
      - mc_proxy: salt-cloud-preinstall
    - require_in:
      - mc_proxy: salt-cloud-postinstall
{% if lxcSettings['cron_sync'] %}
syncron-lxc-ms:
  cron.present:
    - minute: {{lxcSettings.cron_minute}}
    - hour: {{lxcSettings.cron_hour}}
    - name: /usr/bin/mastersalt-run -linfo mc_lxc.sync_images > /dev/null
    - identifier: ms lxc image synchronniser
{% endif %}
{% endmacro %}
{{do(full=False)}}
