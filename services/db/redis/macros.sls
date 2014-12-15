{%- set redisData = salt['mc_redis.settings']() %}
{# 
# Do not forget to use redis_base() macro before using it
# - Create a redis database on a redisd Server 
# - Create a user with the same name as database and all privileges
#}
{%- macro redis_db(db, user=None, password=None,
                     user_creation=True, state_uid=None) -%}
{%- if not state_uid %}
{%-   set state_uid=db.replace('.', '_').replace(' ','_') %}
{%- endif %}
{%- if user_creation -%}
{#- user name is by default the db name #}
{%-   if not user -%}
{%-     set user = db %}
{%-   endif -%}
{%- endif -%}
{#- Important, do not remove this space, needed if the macro is call with "-" 
# we use the user state to in turn create the db (hack ;))#}
makina-redis-db-{{ state_uid }}:
  redis_user.present:
    - database: "{{ db }}"
    - name: "{{ db }}"
    - host: "{{ redisData.redisd.bind_ip}}"
    - passwd: "{{ password }}"
    - port: "{{ redisData.redisd.port}}"
    - user: "{{ redisData.admin }}"
    - password: "{{ redisData.password }}"
    - require_in:
      - mc_proxy: redis-db-create-hook
{%- if user_creation -%}
{{-   redis_user(user, password, state_uid=state_uid, databases=[db])}}
{%- endif %}
{%- endmacro %}

{% macro redis_user(user, password, databases=None, state_uid=None) %}
{%-   if not password -%}
{%-     set password = salt['mc_utils.generate_local_password'](
          'redis_user_{0}_{1}'.format(db, user))%}
{%-   endif -%}
{%- if not databases %}
{#-   global user as superuser #}
{%-   set databases = ['admin'] %}
{%- endif %}
{%- if not state_uid %}
{%-   set state_uid=user.replace('.', '_').replace(' ','_') %}
{%- endif %}
{%-  for db in databases %}
makina-redis-{{db}}create-{{user}}-{{state_uid}}:
  file.managed:
    - name: /etc/redisuser.js
    - source: ''
    - mode: 600
    - user: root
    - contents: |
                redis = new Mongo();
                db = redis.getDB("admin");
                db.auth('{{redisData.admin}}', '{{redisData.password}}');
                db = db.getSiblingDB("{{db}}");
                if (!db.getUser("{{user}}")) {
                  db.createUser({user: "{{user}}",
                                 pwd: "{{password}}",
                                 roles: []});
                }
                db.changeUserPassword("{{user}}", "{{password}}");
                db.grantRolesToUser("{{user}}",
                                    [{role: "dbAdmin", db: "{{db}}"},
                                     {role: "readWrite", db: "{{db}}"},
                                     {role: "read", db: "{{db}}"}]);
  cmd.run:
    - name: redis /etc/redisuser.js;ret=${?};rm -f /etc/redisuser.js;exit ${ret}
    - use_vt: true
    - watch:
      - mc_proxy: redis-post-hardrestart
{%- endfor %}
{% endmacro %}
