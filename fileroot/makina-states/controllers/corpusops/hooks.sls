corpusops-pkg-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: corpusops-pkg-post
corpusops-pkg-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: corpusops-install-pre
      - mc_proxy: corpusops-install-post
      - mc_proxy: corpusops-checkouts-pre
      - mc_proxy: corpusops-checkouts-post
corpusops-install-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: corpusops-install-post
      - mc_proxy: corpusops-checkouts-pre
      - mc_proxy: corpusops-checkouts-post
corpusops-install-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: corpusops-checkouts-pre
      - mc_proxy: corpusops-checkouts-post
corpusops-checkouts-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: corpusops-checkouts-post
corpusops-checkouts-post:
  mc_proxy.hook:
    - watch_in: []
