{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}

{{ localsettings.register('nscd') }}
{% set locs = localsettings.locations %}

nscd-pkgs:
  pkg.installed:
    - pkgs:
      - nscd

nscd-restart:
  cmd.run:
    - name: service nscd restart
    - require:
      - pkg: nscd-pkgs

nscd:
  service.running:
    - enable: True
    - require:
      - cmd: nscd-restart
    - watch:
      - pkg: nscd-pkgs
      - file: touch-etc-nsswitch-conf

touch-etc-nsswitch-conf:
  file.touch:
    - name: {{ locs.conf_dir }}/nsswitch.conf

