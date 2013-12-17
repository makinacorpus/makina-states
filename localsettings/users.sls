# See also makina-states.services.base.ssh.sls
#
# to generate a password hash
# USE ``python -c "import crypt, getpass, pwd; print crypt.crypt('password', '\$6\$SALTsalt\$')"``
# or python
# >>> import crypt, getpass, pwd; print crypt.crypt('password', '$6$SALTsalt$')
#
#
# Idea is to create any user/group needed for ssh managment

{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}

{{ localsettings.register('users') }}
{% set locs = localsettings.locations %}

{% for id, udata in localsettings.users.items() %}
{% set password = udata.get('password', False) %}
{% set home = udata['home'] %}
{{ id }}:
  group.present:
    - name: {{ id }}
    - system: True
  user.present:
    - name: {{ id }}
    - require:
        - group: {{ id }}
    {%- if id not in ['root'] %}
    - fullname: {{ id }} user
    - createhome: True
    - shell: /bin/bash
    - home: {{ home }}
    - gid_from_name: True
    - remove_groups: False
    {% if password %}- password:  {{ password }} {% endif %}
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
