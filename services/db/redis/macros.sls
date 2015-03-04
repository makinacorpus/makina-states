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
