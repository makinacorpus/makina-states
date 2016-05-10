include:
  - makina-states.controllers.hooks
  - makina-states.services.cache.memcached.hooks

makina-states-salt-reqs:
  pkg.installed:
    - pkgs:
      - python
      - git
      - curl
      - locales
      - language-pack-fr
      - language-pack-en
    - watch:
      - mc_proxy: dummy-pre-salt-pkg-pre

    - watch_in:
      - mc_proxy: dummy-pre-salt-pkg-post
