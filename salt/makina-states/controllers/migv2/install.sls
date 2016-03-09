install:
  - cmd.run:
    - name: |
            git clone https://github.com/makinacorpus/makina-states.git -b v2 /srv/makina-states
            cd /srv/makina-states
            ./_scripts/boot-salt.sh -C
      
up_pillar:
  cmd.run:
    - name: |
            sed -i -re "s/rev: stable/rev: v2" /srv/*pillar/*s
