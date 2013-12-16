# See also makina-states.services.base.ssh.sls
#
# to generate a password hash
# USE ``python -c "import crypt, getpass, pwd; print crypt.crypt('password', '\$6\$SALTsalt\$')"``
# or python
# >>> import crypt, getpass, pwd; print crypt.crypt('password', '$6$SALTsalt$')
#
#

# Idea is to create any user/group needed for ssh managment

{% set users={'root': {'admin':True},'sysadmin': {'admin':True},} %}
{%- if grains['os'] == 'Ubuntu' %}
{% set dummy = users.update(
  {'ubuntu': {'admin': True } }
  ) %}
{% endif %}
{% for sid, data in pillar.items() %}
  {% if 'makina-users' in sid %}
    {% set susers=data.get('users', {}) %}
    {% for uid, udata in susers.items() %}
      {% if uid not in users %}
        {% set dummy=users.update({uid: udata})%}
      {% else %}
        {% set u=users[uid] %}
        {% for k, value in udata.items() %}
          {% set dummy=u.update({k: value}) %}
        {% endfor %}
      {% endif %}
    {% endfor%}
  {% endif %}
{% endfor %}

{% for id, udata in users.items() %}
{% set password=udata.get('password', False) %}
{% set home=udata.get('home', '/home/'+id) %}
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
    - home: {{home}}
    - gid_from_name: True
    - remove_groups: False
    {% if password %}- password:  {{password}} {% endif %}
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
