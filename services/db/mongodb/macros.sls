{%- set mongodbData = salt['mc_mongodb.settings']() %}
{# 
# Do not forget to use mongodb_base() macro before using it
# - Create a mongodb database on a mongod Server 
# - Create a user with the same name as database and all privileges
#}
{%- macro mongodb_db(db, user=None, password=None,
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
makina-mongodb-db-{{ state_uid }}:
  mongodb_user.present:
    - database: "{{ db }}"
    - name: "{{ db }}"
    - host: "{{ mongodbData.mongod.bind_ip}}"
    - passwd: "{{ password }}"
    - port: "{{ mongodbData.mongod.port}}"
    - user: "{{ mongodbData.admin }}"
    - password: "{{ mongodbData.password }}"
    - require_in:
      - mc_proxy: mongodb-db-create-hook
{%- if user_creation -%}
{{-   mongodb_user(user, password, state_uid=state_uid, databases=[db])}}
{%- endif %}
{%- endmacro %}

{% macro mongodb_user(user, password, databases=None, state_uid=None) %}
{%-   if not password -%}
{%-     set password = salt['mc_utils.generate_local_password'](
          'mongodb_user_{0}_{1}'.format(db, user))%}
{%-   endif -%}
{%- if not databases %}
{#-   global user as superuser #}
{%-   set databases = ['admin'] %}
{%- endif %}
{%- if not state_uid %}
{%-   set state_uid=user.replace('.', '_').replace(' ','_') %}
{%- endif %}
{%-  for db in databases %}
makina-mongodb-{{db}}create-{{user}}-{{state_uid}}:
  file.managed:
    - name: /etc/mongodbuser.js
    - source: ''
    - mode: 600
    - user: root
    - contents: |
                mongo = new Mongo();
                db = mongo.getDB("admin");
                db.auth('{{mongodbData.admin}}', '{{mongodbData.password}}');
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
    - name: mongo /etc/mongodbuser.js;ret=${?};rm -f /etc/mongodbuser.js;exit ${ret}
    - use_vt: true
    - watch:
      - mc_proxy: mongodb-post-hardrestart
{%- endfor %}
{% endmacro %}
