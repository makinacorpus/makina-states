{#
# Sudoers managment
# see:
#   - makina-states/doc/ref/formulaes/localsettings/sudo.rst
#}

include:
  - makina-states.localsettings.users-hooks

{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'sudo') }}
{%- set locs = salt['mc_localsettings']()['locations'] %}
sudo-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs: [sudo]
    - require_in:
      - mc_proxy: users-ready-hook

sudoers:
   file.managed:
    - name: {{ locs.conf_dir }}/sudoers
    - source: salt://makina-states/files/etc/sudoers
    - mode: 440
    - template: jinja
    - require_in:
      - mc_proxy: users-ready-hook


