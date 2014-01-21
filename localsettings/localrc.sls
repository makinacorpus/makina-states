{#-
# manage /etc/rc.local via helper scripts in /etc/rc.local.d
# goal is to launch tricky services on the end of init processes
#
# Eg launch the firewall only after lxc interfaces are up and so on
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{- localsettings.register('localrc') }}
{%- set locs = localsettings.locations %}
rc-local:
  file.directory:
    - name: {{ locs.conf_dir }}/rc.local.d
    - mode: 0755
    - user: root
    - group: root

rc-local-d:
  file.managed:
    - name: {{ locs.conf_dir }}/rc.local
    - source : salt://makina-states/files/etc/rc.local
    - mode: 0755
    - template: jinja
    - user: root
    - group: root
    - defaults:
      conf_dir: {{ locs.conf_dir }}
