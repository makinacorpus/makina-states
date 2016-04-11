{% set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.controllers.migv2.configs

download:
  cmd.run:
    - name: |
            if [ ! -e {{data.msr}}/.git ] ;then
              git clone https://github.com/makinacorpus/makina-states.git -b v2 {{data.msr}}
            fi
    - watch_in:
      - cmd: merge_configs

install:
  cmd.run:
    - require:
      - cmd: download
      - cmd: merge_configs
    - name: |
            cd {{data.msr}}
            ./_scripts/boot-salt.sh -C
