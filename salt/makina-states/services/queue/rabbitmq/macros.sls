{%- set rabbitmqData = salt['mc_rabbitmq.settings']() %}
{#
# Do not forget to use rabbitmq_base() macro before using it
# - Create a rabbitmq database on a rabbitmqd Server
#}
{%- macro rabbitmq_vhost(db, user=None, password=None,
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
makina-rabbitmq-db-{{ state_uid }}:
  rabbitmq_vhost.present:
    - name: "{{ db }}"
    - watch:
      - mc_proxy: rabbitmq-pre-hardrestart
      - mc_proxy: rabbitmq-post-install
    - require_in:
      - mc_proxy: rabbitmq-db-create-hook

{%- if user_creation -%}
{{-   rabbitmq_user(user, password, state_uid=state_uid,
                    perms=[{db: ['.*', '.*', '.*']}])}}
{%- endif %}
{%- endmacro %}

{% macro rabbitmq_user(user, password, perms=None, state_uid=None, tags=None) %}
{%-   if not password -%}
{%-     set password = salt['mc_utils.generate_local_password'](
          'rabbitmq_user_{0}'.format(user))%}
{%-   endif -%}
{%- if not perms %}
{#-   global user as superuser #}
{%-   set perms = [{'/': ['.*', '.*', '.*']}] %}
{%- endif %}
{%- if not state_uid %}
{%-   set state_uid=user.replace('.', '_').replace(' ','_') %}
{%- endif %}
makina-rabbitmq-create-{{user}}-{{state_uid}}:
  rabbitmq_user.present:
    - name: {{user}}
    - force: true
    - password: {{password}}
    {% if perms%}- perms: {{perms}}{%endif%}
    {% if tags %}- tags: {{tags}}{%endif%}
    - watch:
      - mc_proxy: rabbitmq-post-install
      - mc_proxy: rabbitmq-post-hardrestart
{% endmacro %}
