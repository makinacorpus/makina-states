Generic Installation part of makina-states cloud controller
============================================================

Please have a look to the :ref:`module_mc_cloud_compute_node` module which is where most of this stuff is implemented.

Haproxy
----------
Some notes:

- We use haproxy to load balance the http/https traffics to the vm.
- The ssl termination is on the HAPROXY node !
- We load balance http/https traffic by taking care of using either the `haproxy proxy protocol <http://haproxy.1wt.eu/download/1.5/doc/proxy-protocol.txt>`_ or using regular
  X-Forwarded-For http header (forwardfor haproxy option).

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

SSL & reverse proxy
+++++++++++++++++++
- We do the SSL termination on the haproxy node.
- For this, you will need to setup here the mapping between
  you client certificates and the underlying domains.
- For each node we generate a self signed certificate to assure https connection without the need to have a valid certificate under the hood, but, hay, prefer a valid one.


SSH & reverse proxy
+++++++++++++++++++

    - get the ssh mappings to have an overview of all ssh port mappings::

       mastersalt-call mc_cloud_compute_node.get_ssh_mapping_for_target <compute_node>

    - get the ssh port for a specific vm::

       mastersalt-call mc_cloud_compute_node.get_ssh_port <compute_node> <vm_name>

    - get the reverse proxy settings::

        mastersalt-call mc_cloud_compute_node.get_reverse_proxies_for_target <compute_node>


Automatic grains
-------------------
We enable some grains for the compute not to install itself:

    - makina-states.cloud.is.compute_node
    - makina-states.services.proxy.haproxy
    - makina-states.services.firewall.shorewall

If lxc
    - makina-states.services.virt.lxc
