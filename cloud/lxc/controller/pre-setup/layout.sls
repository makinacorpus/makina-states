include:
  - makina-states.services.cloud.lxc.hooks
{% set cloudSettings = salt['mc_cloud.settings']()%}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
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
        msr: {{cloudSettings.root}}/makina-states
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
        msr: {{cloudSettings.root}}/makina-states
    - watch:
      - mc_proxy: salt-cloud-preinstall
    - watch_in:
      - mc_proxy: salt-cloud-predeploy
