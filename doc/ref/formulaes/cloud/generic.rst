Makina-states cloud generic controller & compute node  & vm documentation
=================================================================================

Controller
~~~~~~~~~~~~
On this node, we mainly do:

    - cloud configuration generation
    - compute node & VMs deployment orchestration
    - SSL managment
    - Maintenance
    - Images store for lxc containers

The SSL certificates managment and centralization
------------------------------------------------------
The generation use and wait for such a layout::

  |- <salt-root>/cloud-controller/ssl
  |    |-<salt-root>/certs/<certname>.pub
  |    |-<salt-root>/certs/wildcards/<certname>.pub
  |
  |- <pillar-root>/cloud-controller/ssl
  |    |-<salt-root>/certs/wildcards/<certname>.pem
  |    |-<salt-root>/certs/<certname>.pem

- The idea is that each controller is tied to a subset of SSL certificates.
  Each domain tied to a controller will need to have a corresponding SSL
  certificate even self signed.
- Corrolary, the cloud controller will also act as the signin certifates authority
  for self signed certificates in this default case of not having a registered
  certificate for a particular domain.
- Each of those certificates will also be tied to one ore more running vms.
- For each domain tied to a compute node, we check for a matching ssl certificate
  existence and generate a self signed one if not existing.
- We distribute those certificates using regular salt file.managed salt://
  prior to reverse proxy configuration for the certicates, and pillar access key
  for private keys.
- The ssl mapping is only be done at generation time and graved inside
  generated sls files for compute nodes.

Compute nodes
~~~~~~~~~~~~~
Responsabilities
-----------------
- Running vms
- Routing network traffic
- Basic network firewalling and redirections
- Reverse proxies
- Any other configured baremetal services

Haproxy
-------
Some notes:

- We use haproxy to load balance the http/https traffics to the vm.
- We generate a configuration file in **/etc/haproxy/extra/cloudcontroller.cfg**.
- The ssl termination is on the HAPROXY node !
- We load balance http/https traffic by taking care of using either the
  `proxy protocol <http://haproxy.1wt.eu/download/1.5/doc/proxy-protocol.txt>`_
  or using regular X-Forwarded-For http header (forwardfor haproxy option).
- For now as the proxy protocol is a bit young, we default to use the
  xforwardedfor method. This is managable as a per vm basis.
- The cloud controller as part of the generation process will have registered
  all SSL certificates to load for the https reverse proxy. We use the new
  haproxy-1.5+ SSL features to load the directory of certificates which we will
  grab from the master.

Settings:

    makina-states.cloud.cloud_compute_node.ssh_port_range_start
        tweak the default ssh allocation port start point
    makina-states.cloud.cloud_compute_node.ssh_port_range_end
        tweak the default ssh allocation port end point

    makina-states.cloud.<provider>.<target>.<vm>.http_proxy_mode
        set to 'xforwardfor' to use xforwardfor (default).
        Setting to something else will use haproxy proxy protocol
        If nothing is set, use xforwardfor for the moment.

**WARNING**, This will bind ports **80** & **443** so it may conflict with any
existing configuration, please double check.

SSL & reverse proxy
+++++++++++++++++++
- We do the SSL termination on the haproxy node.
- For this, you will need to setup here the mapping between
  you client certificates and the underlying domains.
- For each node we generate a self signed certificate to ensure
  https connection without the need to have a valid certificate
  under the hood, but, hay, prefer a valid one.
- We redirect traffic based on the host providen on the request.
- A **X-SSL** header is added on the request for SSL terminated backends.

Inject custom configuration for http reverse proxy
***************************************************
This can be done as usual via pillar

makina-states.cloud.compute_node.conf.<computenode_name>.http_proxy.raw_opts_pre
    insert before generated rules
makina-states.cloud.compute_node.conf.<computenode_name>.http_proxy.raw_opts_post
    insert after generated rules

Exemple::

.. code-block:: yaml

    makina-states.cloud.compute_node.conf.devhost10.local.http_proxy.raw_opts_pre:
      - acl host_myapp.foo.net hdr(host) -i myapp.foo.net
      - use_backend bck_myapp.foo.net if host_myapp.foo.net

You can define the underlying backend also this way

.. code-block:: yaml

    makina-states.services.proxy.haproxy.backends.bck_myapp.foo.net:
        mode: http
        raw_opts:
          - option http-server-close
          - option forwardfor
          - balance roundrobin
        servers:
          - name: srv_myapp.foo.net1
            bind: 10.0.3.7:80
            opts: check

Custom configuration for https reverse proxy
***************************************************
makina-states.cloud.compute_node.conf.<computenode_name>.https_proxy.raw_opts_pre
    insert before generated rules
makina-states.cloud.compute_node.conf.<computenode_name>.https_proxy.raw_opts_post
    insert after generated rules

Exemple::

.. code-block:: yaml

    makina-states.cloud.compute_node.conf.devhost10.local.https_proxy.raw_opts_pre:
      - acl host_myapp.foo.net hdr(host) -i myapp.foo.net
      - use_backend bck_myapp.foo.net if host_myapp.foo.net

You can define the underlying backend also this way

.. code-block:: yaml

    makina-states.services.proxy.haproxy.backends.bck_myapp.foo.net:
        mode: http
        raw_opts:
          - option http-server-close
          - option forwardfor
          - balance roundrobin
        servers:
          - name: srv_myapp.foo.net1
            bind: 10.0.3.7:80
            opts: check


Compute node Automatic grains
--------------------------------
We enable some boolean grains for the compute not to install itself:

    - makina-states.cloud.is.compute_node
    - makina-states.services.proxy.haproxy
    - makina-states.services.firewall.shorewall

If lxc, we also have:

    - makina-states.services.virt.lxc




