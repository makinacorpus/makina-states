{#-
# LXC and shorewall integration, be sure to add
# lxc guests to shorewall running state
# upon creation
# A big sentence to say, restart shorewall
# after each lxc creation to enable
# the container network
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{{- services.register('virt.lxc-shorewall') }}
{%- set localsettings = services.localsettings %}
{%- set locs = localsettings.locations %}
include:
  - {{ services.statesPref }}firewall.shorewall
  - {{ services.statesPref }}virt.lxc

{% for pillark, lxc_data in pillar.items() -%}
{% if pillark.endswith('lxc-server-def')  %}
{% set lxc_name = lxc_data.get('name', pillark.split('-lxc-server-def')[0]) -%}
lxcshorewall-start-{{ lxc_name }}-lxc-service:
  cmd.run:
    - name: /bin/true
    - unless: /bin/true
    - require:
      - cmd: start-{{ lxc_name }}-lxc-service
    - watch_in:
      - cmd: shorewall-restart
{% endif %}
{% endfor %}
