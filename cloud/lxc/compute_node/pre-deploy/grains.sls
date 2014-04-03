{%raw%}{# WARNING THIS STATE FILE IS GENERATED #}{%endraw%}
run-grains:
  grains.present:
    - names:
      - makina-states.services.virt.lxc
      - makina-states.cloud.is.lxchost
    - value: true
reload-grains:
  cmd.script:
    - source: salt://makina-states/_scripts/reload_grains.sh
    - template: jinja
    - watch:
      - grains: run-grains
