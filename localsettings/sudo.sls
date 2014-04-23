{#
# Sudoers managment
# see:
#   - makina-states/doc/ref/formulaes/localsettings/sudo.rst
#}

include:
  - makina-states.localsettings.users-hooks

{{ salt['mc_macros.register']('localsettings', 'sudo') }}
{%- set locs = salt['mc_locations.settings']() %}
sudo-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: [sudo]
    - require_in:
      - mc_proxy: users-ready-hook

{% if salt['mc_controllers.mastersalt_mode']() %}
sudoers:
   file.managed:
    - name: {{ locs.conf_dir }}/sudoers
    - source: salt://makina-states/files/etc/sudoers
    - mode: 440
    - template: jinja
    - require_in:
      - mc_proxy: users-ready-hook
{% endif %}

etc-sudoersd-dir:
  file.directory:
    - name: /etc/sudoers.d
    - mode: 755
