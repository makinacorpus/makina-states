{{ salt['mc_macros.register']('localsettings', 'check_raid') }}
ms-localsettings-install-raid:
  file.managed:
    - source: salt://makina-states/files/usr/bin/install_raid_tools.sh
    - name: /usr/bin/install_raid_tools.sh
    - mode: 755
    - user: root
    - group: root
  cmd.run:
    - name: su -c "/usr/bin/install_raid_tools.sh"
    - use_vt: true
    - require:
      - file: ms-localsettings-install-raid
