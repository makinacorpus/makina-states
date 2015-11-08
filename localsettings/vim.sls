{#-
# vim configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/vim.rst
#}

{{ salt['mc_macros.register']('localsettings', 'vim') }}
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set ugs = salt['mc_usergroup.settings']() %}
{% set vim = salt['mc_vim.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.localsettings.users


{% if vim.full %}
vim-ctags:
  pkg.installed:
    - pkgs:
      - exuberant-ctags
{% endif %}

vim-editor-env-var:
  file.managed:
    - name: /etc/profile.d/vim-editor.sh
    - mode: 755
    - contents: |
                export EDITOR="$(which vim)"
                export ED="$EDITOR"

{% if vim.kiorky_config %}
vim-kiorky-config:
  mc_git.latest:
    - name: https://github.com/kiorky/dotfiles.git
    - target: /etc/kiorky-dotfiles
    - user: root
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

vimrc_configs-append-{{ i }}:
  #cmd.run:
  #  - name: >
  #          sed -i -e "/sts=2 ts=2 ai et tw=0 sw=2/ d" ~/.vimrc &&
  #          sed -i -e "/set sts=4 ts=4 sw=4 ai et nu bg=dark nocompatible/ d" ~/.vimrc &&
  #          sed -i -e "/autocmd! BufRead,BufNewFile *.sls set sts=2 ts=2 ai et tw=0/ d" ~/.vimrc &&
  #          echo "changed=no comment='vimrc edited'"
  #  - user: {{i}}
  #  - stateful: true
  #  - onlyif: test -e ~/.vimrc
  file.accumulated:
    - require:
      #- cmd: vimrc_configs-append-{{ i }}
      - file: vimrc_configs-touch-{{ i }}
      {% if vim.full %}
      - pkg: vim-ctags
      {% endif %}
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

vimrc_configs-touch-global:
  file.managed:
    - name: /etc/vim/vimrc.local
    - source: ''
    - makedirs: true
    - mode: 755
    - user: root
    - group: root

vimrc_configs-append-global:
  #cmd.run:
  #  - name: >
  #          sed -i -e "/sts=2 ts=2 ai et tw=0 sw=2/ d" /etc/vim/vimrc.local &&
  #          sed -i -e "/set sts=4 ts=4 sw=4 ai et nu bg=dark nocompatible/ d" /etc/vim/vimrc.local &&
  #          sed -i -e "/autocmd! BufRead,BufNewFile *.sls set sts=2 ts=2 ai et tw=0/ d" /etc/vim/vimrc.local &&
  #          echo "changed=no comment='vimrc edited'"
  #  - stateful: true
  #  - user: root
  #  - onlyif: test -e /etc/vim/vimrc.local
  file.accumulated:
    - require:
      - file: vimrc_configs-touch-global
      #- cmd: vimrc_configs-append-global
      {% if vim.full %}
      - pkg: vim-ctags
      {% endif %}
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
{% endif %}
