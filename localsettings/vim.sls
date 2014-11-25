{#-
# vim configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/vim.rst
#}

{{ salt['mc_macros.register']('localsettings', 'vim') }}
{% if salt['mc_controllers.mastersalt_mode']() %}
{% set ugs = salt['mc_usergroup.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.localsettings.users

vim-ctags:
  pkg.installed:
    - pkgs:
      - exuberant-ctags

vim-editor-env-var:
  file.managed:
    - name: /etc/profile.d/vim-editor.sh
    - mode: 755
    - contents: |
                export EDITOR="$(which vim)"
                export ED="$EDITOR"

vim-kiorky-config:
  mc_git.latest:
    - name: https://github.com/kiorky/dotfiles.git
    - target: /etc/kiorky-dotfiles
    - user: root

{%- for i, data in ugs.users.items() %}
{%- set home = data['home'] %}
vimrc_configs-touch-{{ i }}:
  file.touch:
    - name: {{ home }}/.vimrc

vimrc_configs-append-{{ i }}:
  cmd.run:
    - name: >
            sed -i -e "/sts=2 ts=2 ai et tw=0 sw=2/ d" ~/.vimrc && 
            sed -i -e "/set sts=4 ts=4 sw=4 ai et nu bg=dark nocompatible/ d" ~/.vimrc && 
            sed -i -e "/autocmd! BufRead,BufNewFile *.sls set sts=2 ts=2 ai et tw=0/ d" ~/.vimrc
    - user: {{i}}
    - onlyif: test -e ~/.vimrc
  file.accumulated:
    - require:
      - file: vimrc_configs-touch-{{ i }}
      - cmd: vimrc_configs-append-{{ i }}
      - pkg: vim-ctags
    - require_in:
      - file: vimrc-config-block-{{i}}
    - filename: {{ home }}/.vimrc
    - text: |
            if filereadable("/etc/kiorky-dotfiles/.vim/load.vim")
            source /etc/kiorky-dotfiles/.vim/load.vim
            else
            set sts=4 ts=4 sw=4 ai et nu bg=dark nocompatible
            autocmd! BufRead,BufNewFile *.sls set sts=2 ts=2 ai et tw=0 sw=2
            endif

vimrc-config-block-{{i}}:
  file.blockreplace:
    - name: {{ home }}/.vimrc
    - marker_start: "\" START managed zone vimrc -DO-NOT-EDIT-"
    - marker_end: "\" END managed zone vimrc -DO-NOT-EDIT-"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
{% endfor %}
{% endif %}
