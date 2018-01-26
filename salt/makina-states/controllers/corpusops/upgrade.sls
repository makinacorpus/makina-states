include:
  - makina-states.controllers.corpusops.hooks 
do-upgrade-corpusops:
  cmd.run:
    - name: bin/install.sh -C -s
    - cwd: /srv/corpusops/corpusops.bootstrap
    - watch:
      - mc_proxy: corpusops-checkouts-pre
    - watch_in:
      - mc_proxy: corpusops-checkouts-post
