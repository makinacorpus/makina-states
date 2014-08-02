{#-
# grub configuration
#}
include:
  - makina-states.localsettings.grub.hooks
{% set data = salt['mc_grub.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'grub') }}
{%  if salt['mc_controllers.allow_lowlevel_states']() %}
{%- if grains['os_family'] in ['Debian'] %}

# disable ifnames & biosdename to avoir interface name twists
# which mess up prepared network topologies
# and static firewalls like shorewall

{% for i in ['/etc/default/grub'] %}
grub-cfg{{i}}:
  file.managed:
    - watch_in:
      - mc_proxy: grub-last-hook
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - name: {{i}}
    - source: salt://makina-states/files{{i}}
{% endfor %}
{% endif %}
{% endif %}
