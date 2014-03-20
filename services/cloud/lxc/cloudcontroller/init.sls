{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
include:
  - makina-states.services.cloud.lxc.hooks
providers_lxc_salt:
  file.managed:
    - watch:
      - mc_proxy: salt-cloud-preinstall
    - watch_in:
      - mc_proxy: salt-cloud-predeploy
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
    - watch:
      - mc_proxy: salt-cloud-preinstall
    - watch_in:
      - mc_proxy: salt-cloud-predeploy
