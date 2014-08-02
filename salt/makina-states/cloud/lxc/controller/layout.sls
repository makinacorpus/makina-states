{% set cloudSettings = salt['mc_cloud.settings']()%}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{#
providers_lxc_salt:
  file.managed:
    - makedirs: true
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
    - makedirs: true
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

#}
remove_old_saltcloud_providers_lxc_salt:
  file.absent:
    - names:
      - {{pvdir}}/makinastates_lxc.conf
      - {{pfdir}}/makinastates_lxc.conf
