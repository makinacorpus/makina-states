{#-
# vim configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/vim.rst
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'vim') }}
{%- set locs = salt['mc_localsettings']()['locations'] %}
include:
  - makina-states.localsettings.users

vim-editor-env-var:
  file.managed:
    - name: /etc/profile.d/vim-editor.sh
    - mode: 755
    - contents: |
                export EDITOR="$(which vim)"
                export ED="$EDITOR"

{%- for i, data in localsettings.users.items() %}
{%- set home = data['home'] %}
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
