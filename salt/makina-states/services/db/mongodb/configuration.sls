{% set data = salt['mc_mongodb.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
include:
  - makina-states.services.db.mongodb.hooks
  - makina-states.services.db.mongodb.services

{% for f in ['/etc/mongod.conf']%}
makina-mongodb-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files{{f}}
    - user: root
    - makedirs: true
    - group: root
    - mode: 744
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
    - watch:
      - mc_proxy: mongodb-pre-conf
    - watch_in:
      - mc_proxy: mongodb-post-conf
{% endfor %}
