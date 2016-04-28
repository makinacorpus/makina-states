{#-
# vim configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/vim.rst
#}

{{ salt['mc_macros.register']('localsettings', 'vim') }}
{% set ugs = salt['mc_usergroup.settings']() %}
{% set vim = salt['mc_vim.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.localsettings.users
  - makina-states.localsettings.editor
  - makina-states.localsettings.vim.hooks

vim-pkgs:
  pkg.installed:
    - pkgs: {{vim.packages}}
    - watch:
      - mc_proxy: vim-pre-install
    - watch_in:
      - mc_proxy: vim-post-install

vim-editor-env-var:
  file.managed:
    - name: /etc/profile.d/vim-editor.sh
    - mode: 755
    - contents: |
                export EDITOR="$(which vim)"
                export ED="$EDITOR"
    - watch:
      - mc_proxy: vim-pre-install
    - watch_in:
      - mc_proxy: vim-post-install

{% if vim.kiorky_config %}
vim-kiorky-config:
  mc_git.latest:
    - name: https://github.com/kiorky/dotfiles.git
    - target: /etc/kiorky-dotfiles
    - user: root
    - watch:
      - mc_proxy: vim-pre-install
    - watch_in:
      - mc_proxy: vim-post-install
{% endif %}

{%- for i, data in ugs.users.items() %}
{%- set home = data['home'] %}
vimrc_configs-touch-{{ i }}:
  file.managed:
    - name: {{ home }}/.vimrc
    - source: ""
    - mode: "644"
    - user: "{{i}}"
    - group: "{{i}}"
    - watch:
      - mc_proxy: vim-pre-install
    - watch_in:
      - mc_proxy: vim-post-install

vimrc_configs-append-{{ i }}:
  file.accumulated:
    - watch:
      - mc_proxy: vim-pre-install
    - watch_in:
      - mc_proxy: vim-post-install
    - require:
      #- cmd: vimrc_configs-append-{{ i }}
      - file: vimrc_configs-touch-{{ i }}
      - pkg: vim-pkgs
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
    - watch:
      - mc_proxy: vim-pre-install
    - watch_in:
      - mc_proxy: vim-post-install
{% endfor %}

vimrc_configs-touch-global:
  file.managed:
    - name: /etc/vim/vimrc.local
    - source: ''
    - makedirs: true
    - mode: 755
    - user: root
    - group: root
    - watch:
      - mc_proxy: vim-pre-install
    - watch_in:
      - mc_proxy: vim-post-install

vimrc_configs-append-global:
  file.accumulated:
    - watch:
      - mc_proxy: vim-pre-install
    - watch_in:
      - mc_proxy: vim-post-install
    - require:
      - file: vimrc_configs-touch-global
      - pkg: vim-pkgs
    - require_in:
      - file: vimrc-config-block-global
    - filename: /etc/vim/vimrc.local
    - text: |
            if filereadable("/etc/kiorky-dotfiles/.vim/load.vim")
            source /etc/kiorky-dotfiles/.vim/load.vim
            else
            set sts=4 ts=4 sw=4 ai et nu bg=dark nocompatible
            autocmd! BufRead,BufNewFile *.sls set sts=2 ts=2 ai et tw=0 sw=2
            endif

vimrc-config-block-global:
  file.blockreplace:
    - name: /etc/vim/vimrc.local
    - marker_start: "\" START managed zone vimrc -DO-NOT-EDIT-"
    - marker_end: "\" END managed zone vimrc -DO-NOT-EDIT-"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - watch:
      - mc_proxy: vim-pre-install
    - watch_in:
      - mc_proxy: vim-post-install
