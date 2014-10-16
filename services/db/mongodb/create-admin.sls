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
    - name: mongo /etc/mongodbuser.js && service mongod restart;ret=${?};rm -f /etc/mongodbuser.js;exit ${ret}
    - unless: echo "use admin"|mongo -u "{{data.admin}}" -p "{{data.password}}"  admin
    - watch:
      - mc_proxy: mongodb-post-hardrestart

makina-mongodb-noanon:
  cmd.run:
    - name: test "x$(echo "JSON.stringify(db.hostInfo())"|mongo admin --quiet|jq .ok)" = "x0"
    - watch:
      - cmd: makina-mongodb-createadmin

makina-mongodb-rootaccess:
  cmd.run:
    - name: test "x$(echo "JSON.stringify(db.hostInfo())"|mongo -u "{{data.admin}}" -p "{{data.password}}" admin --quiet|jq .ok)" = "x1"
    - watch:
      - cmd: makina-mongodb-createadmin
