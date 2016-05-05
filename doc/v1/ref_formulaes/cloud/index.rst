Salt Cloud integration
======================

Introduction
--------------
makina-states include a generic multi-drivers cloud-controller as a large part of a future upper level PaaS project.
Indeed, This is the raw level of the `corpus <https://github.com/makinacorpus/corpus.reactor/blob/master/doc/spec.rst>`_ PaaS project.

At the moment:

    - Bare metal servers are provisionned via the saltify driver
    - LXC container are provisionned via the lxc driver.

In the idea:

    - We have a cloud controller
    - We have compute nodes which are bare metal slaves to host vms.
    - We have vms of a certain virtualization type

- The cloud controller is driver agnostic, and the only thing to support a new technology is
  to add the relevant sls, modules & runners to mimic the awaitened interfaces.

Specifications
--------------
The sequence of makina-states.cloud.generic
+++++++++++++++++++++++++++++++++++++++++++++++++++

makina-states.cloud.generic do all the generic cloud related stuff:

    - On the controller front:

        - run pre configured drivers specific hooks
        - generation of control ssh keys and minion keyss
        - generation and configuration of saltcloud related stuff
        - control of related services like new DNS records
        - run post configured drivers specific hooks

    - On the compute node:

        - run pre configured drivers specific hooks
        - firewalld as the firewall
        - synchronnize/pull any neccessary image or VM templates
        - configure haproxy to load balance http; httpŝ and ssh traffic

            - http/https use standart port
            - ssh use a custom range (40000->50000) and one port is
              allocated for each vm.

        - run post configured drivers specific hooks

    - On the VM driver specific front (each of those steps is hookable (post or
      pre))

        - run pre configured drivers specific hooks
        - spawn the new minion via the compute node
        - install default users
        - install marker grains
        - install the cloud controller ssh key on the vm
        - run highstate on the new vm
        - ping the new minion
        - run post configured drivers specific hooks

    - On the compute node & vms (post provision):

        - Any task remaining to make the newly VM minion a good citizen.

    - On the compute node & vms (post vm provisions):

        - Any task remaining to make the newly VM minion a good citizen.

See :ref:`form_cloud_lxc` for an exemple

How
++++
Basically the interface with this cloud controller is done:

    - Via the ``pillar`` for configuratioin

    - Via ``execution modules`` to make settings structures and some specific stuff
      like SSL certificate generation. They are heavily used by the runners.

    - Via ``runner modules`` to make actions on controller, compute_nodes and
      vms.

        - The runner may in turn execute **slses** from the makina-states.cloud
          directory on the controller or on a compute_node or on a vm.


.. toctree::
   :maxdepth: 2

   usage.rst


