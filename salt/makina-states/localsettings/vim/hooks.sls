include:
  - makina-states.localsettings.editor.hooks
  - makina-states.localsettings.users.hooks

vim-pre-install:
  mc_proxy.hook:
    - watch:
      - mc_proxy: users-ready-hook
    - watch_in:
      - mc_proxy: vim-post-install

vim-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: editor-pre-install
