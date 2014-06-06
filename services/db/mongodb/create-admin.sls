{% set data = salt['mc_mongodb.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.db.mongodb.hooks

makina-mongodb-createadmin:
  file.managed:
    - name: /etc/mongodbuser.js
    - source: ''
    - mode: 600
    - user: root
    - contents: |
                db = new Mongo().getDB("admin");
                db.createUser({
                    user: "{{data.admin}}",
                    pwd: "{{data.password}}",
                    roles: [
                      {role: "userAdminAnyDatabase", db: "admin"},
                      {role: "root", db: "admin"}
                      ]})
  cmd.run:
    - name: mongo /etc/mongodbuser.js && service mongod restart
    - onlyif: echo "use admin"|mongo
    - watch:
      - mc_proxy: mongodb-post-hardrestart
