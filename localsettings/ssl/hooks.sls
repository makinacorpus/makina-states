ssl-certs-pre-hook:
  mc_proxy.hook:
    - watch_in:
      mc_proxy: ssl-certs-post-hook
ssl-certs-post-hook:
  mc_proxy.hook: []
