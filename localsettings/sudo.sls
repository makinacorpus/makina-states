{#
# Sudoers managment
# see:
#   - makina-states/doc/ref/formulaes/localsettings/sudo.rst
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'sudo') }}
{%- set locs = localsettings.locations %}
sudo-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs: [sudo]

sudoers:
   file.managed:
    - name: {{ locs.conf_dir }}/sudoers
    - source: salt://makina-states/files/etc/sudoers
    - mode: 440
    - template: jinja

{% for i in localsettings.sudoers %}
add-user-sudoers:
  user.present
    - name: {{i}}
    - remove_groups: False
    - optional_groups:
      - sudo
{% endfor %}
