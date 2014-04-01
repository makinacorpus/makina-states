Makina-states cloud controller & compute node documentation
============================================================

Please have a look which some places  most of this stuff is implemented:

    - :ref:`module_mc_cloud`
    - :ref:`module_mc_cloud_controller`
    - :ref:`module_mc_cloud_compute_node`

Controller
~~~~~~~~~~~~
On this node, we mainly do:

    - cloud configuration generation
    - compute node & VMs deployment orchestration
    - SSL managment
    - Maintenance

The cloud configuration generation
-----------------------------------
The SSL certificates managment and centralization
------------------------------------------------------
- The idea is that each controller is tied to a subset of SSL certificates.
- The cloud controller will also act as the signin certifates authority
  for self signed certificates.
- Each of those certificates will also be tied to one ore more running vms.
- We will at least have one valid certicate per node.
- We distribute those certificates using regular salt file.managed salt://
  prior to reverse proxy configuration.

Compute nodes
~~~~~~~~~~~~~~
Haproxy
----------
Some notes:

- We use haproxy to load balance the http/https traffics to the vm.
- We generate a configuration file in **/etc/haproxy/extra/cloudcontroller.cfg**.
- The ssl termination is on the HAPROXY node !
- We load balance http/https traffic by taking care of using either the
  `proxy protocol <http://haproxy.1wt.eu/download/1.5/doc/proxy-protocol.txt>`_
  or using regular X-Forwarded-For http header (forwardfor haproxy option).

- For now as the proxy protocol is a bit young, we default to use the
  xforwardedfor method. This is managable as a per vm basis.

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

Inject custom configuration for http reverse proxy
***************************************************
This can be done as usual via pillar

makina-states.cloud.compute_node.conf.<computenode_name>.http_proxy.raw_opts_pre
    insert before generated rules
makina-states.cloud.compute_node.conf.<computenode_name>.http_proxy.raw_opts_post
    insert after generated rules

Exemple

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

Then regenerate your cloud configuration, example::

    mastersalt-call state.sls makina-states.cloud.generate

And apply your reverse proxy configuration, example::

    mastersalt-call state.sls cloud-controller.compute_node.devhost10local.run-compute_node_reverseproxy

Inject custom configuration for https reverse proxy
***************************************************
makina-states.cloud.compute_node.conf.<computenode_name>.https_proxy.raw_opts_pre
    insert before generated rules
makina-states.cloud.compute_node.conf.<computenode_name>.https_proxy.raw_opts_post
    insert after generated rules

Exemple

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

Then regenerate your cloud configuration, example::

    mastersalt-call state.sls makina-states.cloud.generate

And apply your reverse proxy configuration, example::

    mastersalt-call state.sls cloud-controller.compute_node.devhost10local.run-compute_node_reverseproxy


Dont forget to replace devhost10.local by your compute_node target.

Settings of a compute node
--------------------------
Global settings
++++++++++++++++++
    - know what vms we have for all targets::


        mastersalt-call mc_cloud_compute_node.get_vms <compute_node>

    - know what vms we have for all targets::

        mastersalt-call mc_cloud_compute_node.get_vms <compute_node>

    - only for a specific host::

        mastersalt-call mc_cloud_compute_node.get_vms_for_target <compute_node>

    - know the detailed vm settings::

        mastersalt-call mc_cloud_compute_node.get_settings_for_target <compute_node>

SSH & reverse proxy
+++++++++++++++++++

    - get the ssh mappings to have an overview of all ssh port mappings::

       mastersalt-call mc_cloud_compute_node.get_ssh_mapping_for_target <compute_node>

    - get the ssh port for a specific vm::

       mastersalt-call mc_cloud_compute_node.get_ssh_port <compute_node> <vm_name>

    - get the reverse proxy settings::

        mastersalt-call mc_cloud_compute_node.get_reverse_proxies_for_target <compute_node>


Compute node Automatic grains
--------------------------------
We enable some boolean grains for the compute not to install itself:

    - makina-states.cloud.is.compute_node
    - makina-states.services.proxy.haproxy
    - makina-states.services.firewall.shorewall

If lxc, we also have:

    - makina-states.services.virt.lxc


