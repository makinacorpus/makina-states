Use a lxc based makina-states environment
==========================================

In makina-states, our LXC images are known to use a network bridge called
``lxcbr1``.

They use the ``10.5/16`` network and ``10.5.0.1`` as the default gateway.

For this to work, you have plenty of solutions.


.. toctree::
   :maxdepth: 1

   install_ubuntu.rst
   install_systemd.rst
