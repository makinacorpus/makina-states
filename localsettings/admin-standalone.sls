{#- #}
{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{% set locs=localsettings.locations %}
{% macro do(full=False ) %}
{{ salt['mc_macros.register']('localsettings', 'admin') }}
include:
  - makina-states.localsettings.users-hooks
{% if full %}
  - makina-states.localsettings.users
  - makina-states.localsettings.sudo
{% endif %}
{% if localsettings.root_password %}
ms-add-root-password:
  user.present:
    - name: root
    - password: {{localsettings.root_password}}
    - remove_groups: False
{% endif %}
{% for i in localsettings.sudoers %}
ms-add-user-{{i}}-sudoers:
  user.present:
    - require:
      - mc_proxy: users-ready-hook
    - name: {{i}}
    - remove_groups: False
    - optional_groups:
      - sudo
{% endfor %}
{% for i in localsettings.defaultSysadmins %}
ms-add-user-{{i}}-sudoers:
  user.present:
    - require:
      - mc_proxy: users-ready-hook
    {% if localsettings.sysadmin_password %}
    - password: {{localsettings.sysadmin_password}}
    {% endif %}
    - name: {{i}}
    - remove_groups: False
    - optional_groups:
      - sudo
{% endfor %}
{% for user in localsettings.defaultSysadmins %}
{%- for key in localsettings.sysadmins_keys %}
ssh_auth-rootkey-{{user}}-{{key}}:
  ssh_auth.present:
    - user: root
    - source: salt://files/ssh/{{ key }}
    - require:
      - mc_proxy: users-ready-hook
ssh_auth-sysadminkey-{{user}}-{{key}}:
  ssh_auth.present:
    - user: {{ user }}
    - source: salt://files/ssh/{{ key }}
    - require:
      - mc_proxy: users-ready-hook
{%-    endfor %}
{%-  endfor %}
{% endmacro %}
{{ do(full=False) }}
