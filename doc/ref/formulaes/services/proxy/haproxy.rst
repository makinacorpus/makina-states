haproxy
========
Configure haproxy, see the salt :ref:`module_mc_haproxy` module to know which option to configure in pillar.
There are shortcut modes to ease the configuration, please see bellow

Exposed hooks
-----------------
- haproxy-pre-install-hook
- haproxy-post-install-hook
- haproxy-pre-conf-hook
- haproxy-post-conf-hook
- haproxy-pre-restart-hook
- haproxy-post-restart-hook

Example: http reverse proxy based on domain name
--------------------------------------------------
Add the following entries to your pillar and re run the haproxy states


.. code-block:: yaml

    makina-states.services.proxy.haproxy.frontends.myapp.domain.com:
      mode: http
      bind: ':80'
      raw_opts:
        - acl host_myapp.domain.com hdr(host) -i myapp.domain.com
        - use_backend bck_myapp.domain.com if host_myapp.domain.com

.. code-block:: yaml

    makina-states.services.proxy.haproxy.backends.bck_myapp.domain.com:
        mode: http
        raw_opts:
          - option http-server-close
          - option forwardfor
          - balance roundrobin
        servers:
          - name: srv_myapp.domain.com1
            bind: 10.0.3.7:80
            opts: check

this will configure a reverse proxy for domain myapp.domain.com on port 80 -> 10.0.3.7 port 80.


