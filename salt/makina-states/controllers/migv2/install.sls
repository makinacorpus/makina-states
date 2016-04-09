include:
  - makina-states.controllers.migv2.configs

download:
  cmd.run:
    - name: |
            git clone https://github.com/makinacorpus/makina-states.git -b v2 /srv/makina-states
    - watch_in:
      - cmd: merge_configs

install:
  cmd.run:
    - require:
      - cmd: download
      - cmd: merge_configs
    - name: |
            cd /srv/makina-states
            ./_scripts/boot-salt.sh -C
