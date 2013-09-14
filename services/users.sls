# see also ssh.sls

# Idea is to create any user/group needed for ssh managment

{% set users = {'root': {'admin':True},'sysadmin': {'admin':True},} %}
{%- if grains['os'] == 'Ubuntu' %}
{% set nodo = users.update({'ubuntu': {'admin':True}}) %}
{% endif %}
{% for sid, sshdata in pillar.items() %}
  {% if 'makina-users' in sid %}
    {% set susers = sshdata.get('users', []) %}
    {% for uid in susers %}
      {% if uid not in users %}
        {% set dummy = users.update({uid: {}})%}
      {% endif %}
    {% endfor%}
  {% endif %}
{% endfor %}
{% for id, udata in users.items() %}
{{id}}:
  group.present:
    - name: {{ id }}
    - system: True
  user.present:
    - name: {{ id}}
    - require:
        - group: {{ id }}
    {%- if id not in ['root'] %}
    - fullname: {{ id }} user
    - createhome: True
    - shell: /bin/bash
    - home: /home/{{ id }}
    - gid_from_name: True
    - remove_groups: False
    - optional_groups:
      - {{ id }}
      - cdrom
      - audio
      - dip
      - plugdev
      - games
      - sambashare
      {%- if udata.get('admin', False) %}
      - lpadmin
      - sudo
      - adm
      {%- if grains['os_family'] != 'Debian' %}
      - admin
      - wheel
      {% endif %}
{% endif %}
{% endif %}
{% endfor %}
