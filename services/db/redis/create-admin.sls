{% set data = salt['mc_redis.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.db.redis.hooks

makina-redis-createadmin:
  file.managed:
    - name: /etc/redisuser.js
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
    - name: redis /etc/redisuser.js && service redisd restart;ret=${?};rm -f /etc/redisuser.js;exit ${ret}
    - unless: echo "use admin"|redis -u "{{data.admin}}" -p "{{data.password}}"  admin
    - watch:
      - mc_proxy: redis-post-hardrestart

makina-redis-noanon:
  cmd.run:
    - name: test "x$(echo "JSON.stringify(db.hostInfo())"|redis admin --quiet|jq .ok)" = "x0"
    - watch:
      - cmd: makina-redis-createadmin

makina-redis-rootaccess:
  cmd.run:
    - name: test "x$(echo "JSON.stringify(db.hostInfo())"|redis -u "{{data.admin}}" -p "{{data.password}}" admin --quiet|jq .ok)" = "x1"
    - watch:
      - cmd: makina-redis-createadmin
