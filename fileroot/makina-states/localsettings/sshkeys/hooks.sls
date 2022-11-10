localsettings-ssh-keys-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: localsettings-ssh-keys-post
localsettings-ssh-keys-post:
  mc_proxy.hook: []

