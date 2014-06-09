{#
# Base users for the ownership of backup filesystem files
# and related apps
#}

{%- for user in ['fs', 'db'] %}
{%- set name = user+'-backup'  %}
backup-user-{{name}}:
  group.present:
    - name: {{name}}
    - system: True
  user.present:
    - name: {{name}}
    - shell: /bin/bash
    - require:
      - group: backup-user-{{name}}
    - fullname: {{name}}user
    - gid_from_name: True
    - remove_groups: False
{% endfor %}
