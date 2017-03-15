Install & configure the cloud ecosystem: Using salt runners
==============================================================

When you pillar is ready for action, you next step is to send a command to provision and configure your infrastructure nodes.

Runners overview
-------------------------------------------------------
This is in order how is configured each part of the cloud.
This can help you to understand, debug & learn how to act on your cloud.

Configure the controller
+++++++++++++++++++++++++++
If you want to only install the controller configuration, just do::

    mastersalt-run -lall mc_cloud_controller.orchestrate no_saltify=True no_provision=true

This is a good idea to do that when there is a long time you did not touched to
it.

Saltify any compute node
+++++++++++++++++++++++++
The next step would certainly be to attach the compute nodes::

    mastersalt-run -lall mc_cloud_controller.orchestrate no_configure=True no_provision=true

The next step would certainly be to attach via saltify a specific node::

    mastersalt-run -lall mc_cloud_controller.orchestrate no_configure=True no_provision=true only=[minionid]

Configure the compute node
++++++++++++++++++++++++++++++++
After having the compute node linked, you can begin to configure it to host your
VMs::

    mastersalt-run -lall mc_cloud_compute_node.orchestrate  only=[minionid] only_vms=[vm_id]

Is equivalent and you have better to use::

    mastersalt-run -lall mc_cloud_controller.orchestrate only=[minionid] only_vms=[vm_id] no_dns_conf=True no_configure=True no_saltify=True

This call ``provision_compute_nodes`` which in turn calls all
``compute_node`` related stuff which will run generic and per drivers specific
hooks (firewall, loadbalancer, driver images sync, etc.).

**only** and **only_vms** are optionals but recommended to limit the scope of your commands.

Spawning and running vm post-configuration
++++++++++++++++++++++++++++++++++++++++++

Eg to provision only bar::

    mastersalt-run -lall mc_cloud_controller.orchestrate only=[foo] only_vms=[bar] no_compute_node_provision=true

Is equivalent to::

    mastersalt-run -lall mc_cloud_vm.orchestrate only=[bar]

**only** and **only_vms** are optionals but recommended to limit the scope of your commands.


Runners reference links
------------------------
Runners:
+++++++++++

    - :ref:`module_mc_cloud`
    - :ref:`module_mc_cloud_controller`
    - :ref:`module_mc_cloud_compute_node`
    - :ref:`runner_mc_api`
    - :ref:`runner_mc_cloud_controller`
    - :ref:`runner_mc_cloud_compute_node`
    - :ref:`runner_mc_cloud_saltify`
    - :ref:`runner_mc_cloud_vm`
    - :ref:`runner_mc_cloud_lxc`
    - :ref:`runner_mc_cloud_kvm`

Configuration modules
++++++++++++++++++++++

    - :ref:`module_mc_cloud`
    - :ref:`module_mc_cloud_compute_node`
    - :ref:`module_mc_cloud_controller`
    - :ref:`module_mc_cloud_compute_node`
    - :ref:`module_mc_cloud_saltify`
    - :ref:`module_mc_cloud_lxc`


Helpers
++++++++

    - :ref:`runner_mc_api`


Further implementation reference
----------------------------------
.. toctree::
   :maxdepth: 2

   generic.rst
   lxc.rst
   saltify.rst



