include:
  - makina-states.controllers.corpusops.hooks
do-corpusops-reqs:
  pkg.installed:
    - pkgs:
      - git
      - python
      - curl
    - unless: which git && which python && which curl
    - watch:
      - mc_proxy: corpusops-pkg-pre
    - watch_in:
      - mc_proxy: corpusops-pkg-post
do-install-corpusops:
  mc_git.latest:
    - name: https://github.com/corpusops/corpusops.bootstrap.git
    - target: /srv/corpusops/corpusops.bootstrap
    - onlyif: test ! -e /srv/corpusops/corpusops.bootstrap/.git
    - watch:
      - mc_proxy: corpusops-install-pre
    - watch_in:
      - mc_proxy: corpusops-install-post
  cmd.run:
    - name: bin/install.sh -C
    - cwd: /srv/corpusops/corpusops.bootstrap
    - onlyif: test ! -e venv/bin/ansible
    - watch:
      - mc_git: do-install-corpusops
      - mc_proxy: corpusops-install-pre
    - watch_in:
      - mc_proxy: corpusops-install-post
