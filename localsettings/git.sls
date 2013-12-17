{% import "makina-states/_macros/vars.jinja" as vars with context %}
include:
  - makina-states.localsettings.users

{% for i, data in vars.users.items() %}
{% set home = data['home'] %}

gitorious_base_ssh_configs-group-{{ i }}:
  file.directory:
    - name: {{ home }}/.ssh
    - mode: 0700
    - user: {{i}}
    - makedirs: True
    - require:
      - user: {{ i }}

gitorious_base_ssh_configs-touch-{{ i }}:
  file.touch:
    - name: {{ home }}/.ssh/config
    - require:
      - file: gitorious_base_ssh_configs-group-{{ i }}

gitorious_base_ssh_configs-append-{{ i }}:
  file.append:
    - require:
      - file: gitorious_base_ssh_configs-touch-{{ i }}
    - name : {{ home }}/.ssh/config
    - user: {{i}}
    - text: |
            # entry managed via salt !
            host=    gitorious.makina-corpus.net
            HostName=gitorious.makina-corpus.net
            Port=2242
{% endfor %}

global-git-config:
  file.managed:
    - name: /etc/gitconfig
    - source: salt://makina-states/files/etc/gitconfig
    - mode: 755
    - template: jinja
