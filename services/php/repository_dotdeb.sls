makina-dotdeb-add-key:
  cmd.watch:
    - name: wget -q -O - http://www.dotdeb.org/dotdeb.gpg | sudo apt-key add -
    - unless: apt-key adv --list-keys E9C74FEEA2098A6E

makina-dotdeb-apt-update:
  cmd.run:
    - name: apt-get update
    - require:
      - cmd: makina-dotdeb-add-key
    - watch_in:
      - file: makina-dotdeb-repository
      - file: makina-dotdeb-pin-php

makina-makina-dotdeb-repository:
  file.managed:
    - name: /etc/apt/sources.list.d/dotdeb.org.list
    - mode: 0644
    - user: root
    - group: root
    - template: jinja
    - source: salt://makina-states/files/etc/apt/sources.list.d/dotdeb.org.list

makina-dotdeb-pin-php:
  file.managed:
    - name: /etc/apt/preferences.d/dotdeb.org
    - mode: 0644
    - user: root
    - group: root
    - template: jinja
    - source: salt://makina-states/files/etc/apt/preferences.d/dotdeb.org

