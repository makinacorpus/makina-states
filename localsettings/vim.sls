include:
  - makina-states.localsettings.users

{% set vimrc_default_users = ['root', 'sysadmin'] %}
{% if grains['os'] == 'Ubuntu' %}
  {% set dummy = vimrc_default_users.append('ubuntu') %}
{% endif %}
{% for i in vimrc_default_users %}
{% set home = "" %}
{% if i != "root" %}
{% set home = "/home" %}
{% endif %}
{% set home = home + "/" + i %}
vimrc_configs-touch-{{ i }}:
  file.touch:
    - name: {{ home }}/.vimrc

vimrc_configs-append-{{ i }}:
  file.append:
    - require:
      - file.touch: vimrc_configs-touch-{{ i }}
    - name : {{ home }}/.vimrc
    - text: |
            set sts=4 ts=4 sw=4 ai et nu bg=dark nocompatible
            autocmd! BufRead,BufNewFile *.sls set sts=2 ts=2 ai et tw=0 sw=2

vimrc_configs-append-{{ i }}-1:
  file.append:
    - require:
      - file.touch: vimrc_configs-touch-{{ i }}
    - name : {{ home }}/.vimrc
    - text: syntax on
{% endfor %}
