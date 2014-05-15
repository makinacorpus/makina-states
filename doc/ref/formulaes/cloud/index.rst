Salt Cloud integration
======================

makina-states include a generic multi-drivers cloud-controller as a part of an upper level PaaS project.
Indeed, This is the raw level of the `corpus <https://github.com/makinacorpus/corpus.reactor/blob/master/doc/spec.rst>`_ PaaS project.

At the moment:

    - LXC container are provisionned via the lxc driver.
    - Bare metal servers are provisionned via the saltify driver

In the idea:

    - We have a cloud controller
    - We have compute nodes which are bare metal slaves to host vms.
      The driver of a compute node would then  be specialised to install
      a configure a virtualisation technology (eg: kvm,
      lcx)
    - We have vms which are specialized to deploy a specific driver.
      (eg: lxc container)

- The cloud controller is driver agnostic, and the only thing to support a new technology is to add the relevant sls, modules & runners  to mimic the awaitened interface.

The sequence:

    - On the controller front:

        - generation of control ssh keys and minion keyss
        - generation and configuration of saltcloud related stuff
        - control of related services like new DNS records

    - On the compute node:

        - shorewall as the firewall
        - haproxy to load balance http; httpŝ and ssh traffic

            - http/https use standart port
            - ssh use a custom range (40000->50000) and one port is
              allocated for each vm.

    - On the driver specific front

        - spawn the new minion via the compute node
        - install default users
        - install marker grains
        - install the cloud controller ssh key on the vm
        - run highstate on the new vm

    - On the compute node & vms:

        - Any task remaining to make the newly VM minion a good citizen.

Basically the interface with this cloud controller is done:

    - Via runner modules to make action on controller, compute_nodes and vms

        - The runner may in turn execute slses from the makina-states.cloud
          directory on the controller or on a compute_node or on a vm.

    - Via generic modules to make settings structures and some specific stuff
      like SSL certificate generation.

.. toctree::
   :maxdepth: 2

   generic.rst
   lxc.rst
   saltify.rst
