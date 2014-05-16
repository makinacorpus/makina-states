Install & configure the cloud ecosystem: Using salt runners
==============================================================

Individual steps (doing manual or partial installation)
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

    mastersalt-run -lall mc_cloud_controller.orchestrate no_configure=True no_saltify=True no_vms=True only=[minionid]

Is equivalent to (this call this one in fact)::

    mastersalt-run -lall mc_cloud_compute_node.orchestrate no_vms=True only=[minionid]

- This will call in turn the ``mc_cloud_compute_node.orchestrate`` funcion.
- 'mc_cloud_compute_node' will in turn call ``mc_cloud_vm.orchestrate`` function
  if you do not filter out vms provision.

This call ``provision_compute_nodes`` which in turn calls all
``compute_node``related stuff.


And the steps one by one::


 
