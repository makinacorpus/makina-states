install-raid:
  mc_proxy.hook: []
{% if pillar.get('makina-states.nodetypes.check_raid', False) %}
  file.managed:
    - source: salt://makina-states/files/usr/bin/install_raid_tools.sh
    - name: /usr/bin/install_raid_tools.sh
    - mode: 755
    - user: root
    - group: root
  cmd.run:
    - name: /usr/bin/install_raid_tools.sh
    - use_vt: true
    - require:
      - file: install-raid
{% endif %}
