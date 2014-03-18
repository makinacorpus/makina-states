Salt Cloud integration
======================
Each of those module can be used independently from each other, idea is to provision all machines an VMs via salt-cloud and nothing will then be done by hand from end to end.

At the moment:

    - LXC container are provisionned via the lxc driver.
    - Bare metal servers are provisionned via the saltify driver

.. toctree::
   :maxdepth: 2

   lxc.rst
   saltify.rst
