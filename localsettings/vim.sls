include:
  - makina-states.localsettings.users
{% import "makina-states/_macros/vars.jinja" as vars with context %}
{% for i, data in vars.users %}
{% set home = data['gome'] %}
vimrc_configs-touch-{{ i }}:
  file.touch:
    - name: {{ home }}/.vimrc

vimrc_configs-append-{{ i }}:
  file.append:
    - require:
      - file: vimrc_configs-touch-{{ i }}
    - name : {{ home }}/.vimrc
    - text: |
            set sts=4 ts=4 sw=4 ai et nu bg=dark nocompatible
            autocmd! BufRead,BufNewFile *.sls set sts=2 ts=2 ai et tw=0 sw=2

vimrc_configs-append-{{ i }}-1:
  file.append:
    - require:
      - file: vimrc_configs-touch-{{ i }}
    - name : {{ home }}/.vimrc
    - text: syntax on
{% endfor %}
