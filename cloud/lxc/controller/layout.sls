include:
  - makina-states.cloud.generic.hooks.controller
{% set cloudSettings = salt['mc_cloud.settings']()%}
{% set lxcSettings = salt['mc_cloud_lxc.settings']()%}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
providers_lxc_salt:
  file.managed:
    - watch:
      - mc_proxy: cloud-generic-controller-pre-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-controller-post-post-deploy
    - source: salt://makina-states/files/etc/salt/cloud.providers.d/makinastates_lxc.conf
    - name: {{pvdir}}/makinastates_lxc.conf
    - user: root
    - template: jinja
    - group: root
    - defaults:
        data: |
              {{salt['mc_utils.json_dump'](lxcSettings.defaults)}}
        cdata: |
               {{salt['mc_utils.json_dump'](cloudSettings)}}
        vms: |
             {{salt['mc_utils.json_dump'](lxcSettings.vms.keys())}}
        msr: {{cloudSettings.root}}/makina-states
profiles_lxc_salt:
  file.managed:
    - template: jinja
    - source: salt://makina-states/files/etc/salt/cloud.profiles.d/makinastates_lxc.conf
    - name: {{pfdir}}/makinastates_lxc.conf
    - user: root
    - group: root
    - defaults:
        pdata: |
               {{salt['mc_utils.json_dump'](lxcSettings.defaults)}}
        cdata: |
               {{salt['mc_utils.json_dump'](cloudSettings)}}
        profiles: |
                  {{salt['mc_utils.json_dump'](lxcSettings.lxc_cloud_profiles)}}
        vms: |
             {{salt['mc_utils.json_dump'](lxcSettings.vms.keys())}}
        msr: {{cloudSettings.root}}/makina-states
    - watch:
      - mc_proxy: cloud-generic-controller-pre-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-controller-post-post-deploy

