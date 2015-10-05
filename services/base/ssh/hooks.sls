{# hooks for openssh #}
{#- hook after all keys for defined by all defined users are dropped in home folders #}
ssh-post-user-keys:
  mc_proxy.hook: []
ssh-service-prerestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ssh-service-postrestart
ssh-service-postrestart:
  mc_proxy.hook: []
