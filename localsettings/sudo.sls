{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{- localsettings.register('sudo') }}
{%- set locs = localsettings.locations %}
sudo-pkgs:
  pkg.installed:
    - pkgs: [sudo]

sudoers:
   file.managed:
    - name: {{ locs.conf_dir }}/sudoers
    - source: salt://makina-states/files/etc/sudoers
    - mode: 440
    - template: jinja
