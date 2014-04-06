lxc-initial-highstate:
  cmd.run:
    - name: ssh {{vmname}} {{cloudSettings.root}}/makina-states/_scripts/boot-salt.sh --initial-highstate
    - user: root
