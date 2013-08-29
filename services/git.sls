{% set ssh_default_users = ['root', 'sysadmin'] %}
{% if grains['os'] == 'Ubuntu' %}
  {% set dummy = ssh_default_users.append('ubuntu') %}
{% endif %}
{% for i in ssh_default_users %}
{% set home = "" %}
{% if i != "root" %}
{% set home = "/home" %}
{% endif %}
{% set home = home + "/" + i %}
gitorious_base_ssh_configs-group-{{ i }}:
  file.directory:
    - name: {{ home }}/.ssh
    - mode: 0700
    - makedirs: True
    - require:
      - user: {{ i }}

gitorious_base_ssh_configs-touch-{{ i }}:
  file.touch:
    - name: {{ home }}/.ssh/config
    - require:
      - file.directory: gitorious_base_ssh_configs-group-{{ i }}

gitorious_base_ssh_configs-append-{{ i }}:
  file.append:
    - require:
      - file.touch: gitorious_base_ssh_configs-touch-{{ i }}
    - name : {{ home }}/.ssh/config
    - text: |
            # entry managed via salt !
            host=    gitorious.makina-corpus.net
            HostName=gitorious.makina-corpus.net
            Port=2242
{% endfor %}
