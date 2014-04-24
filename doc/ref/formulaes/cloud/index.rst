Salt Cloud integration
======================

makina-states include a generic multi drivers cloud-controller as a part of an upper level PaaS project.
Indeed, This is the raw level of the `corpus <https://github.com/makinacorpus/corpus.reactor/blob/master/doc/spec.rst>`_ PaaS project.

At the moment:

    - LXC container are provisionned via the lxc driver.
    - Bare metal servers are provisionned via the saltify driver

In the idea:

    - We have a cloud controller
    - We have compute nodes which are bare metal slaves to host vms
    - We have vms

- The cloud controller is driver agnostic, and the only thing to support a new technology is to add the relevant sls to mimic the awaitened interface.
- Basically we do:

    - predeploy

        - stuff to do on the controller and on the compute node before the vm can be spawned
        - The cloud controller will install and require both a minion and a SSH key to have both SSH and salt control.
        - The cloud controller will configure the compute node reverse proxy & firewalls.
          For now we use:

            - shorewall as the firewall
            - haproxy to load balance http; httpŝ and ssh traffic

                - http/https use standart port
                - ssh use a custom range (40000->50000) and one port is
                  allocated for each vm.

    - deploy

        - The actions for the VM to be spawn and rattached to the cloud
          controller (mainly executing the cloud.profile state)

    - post-deploy

        - Any task remaining to make the newly VM minion a good citizen.

            - highstate
            - install default users
            - install marker grains
            - install the cloud controller ssh key on the vm


As we want the cloud controller the less possible service dependant, the cloud installation is done in 2 phases.

    - We in the first place generate all the cloud configuration states
      in <salt-root>/cloud-controller/<compute_node_id>.
      You can see that a lot of sls will be generated in this place.
    - In a second time, we can run specific states in this directory to finish the installation.

.. toctree::
   :maxdepth: 2

   generic.rst
   lxc.rst
   saltify.rst
