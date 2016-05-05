Salt
====

Those utilities have the following goals:

    - Generate the hooks for orchestration purpose (macro: salt_dummies)
    - Install makina states with our custom layout (macro: install_makina_states)
    - Configure a salt master using this layout (macro: install_master)
    - Configure a salt minion using this layout (macro: install_minion)

They are used in the base **controllers** states to install the (**master**)salt daemons.

All of the layout and base parameters can be controlled at state & pillar level

Three macros are exposed:

  - install_makina_states: install the common saltstack stuff
  - install_master: master specific bits
  - install_minion: minion specific bits

We extensivly use the **mc_services** & the **mc_salt** modules registries.

Common values must be updated in the common section, and the same for **master** or **minion** sections.

To override values in pillar
.. code-block:: yaml

    salt:
       common:
         - prefix: /foobar
       master:
         - ret_port: 4706
       minion:
         - master_port: 4706
    mastersalt:
       common:
         - prefix: /foobar/mastersalt
       master:
         - ret_port: 4506
       minion:
         - master_port: 4506

Formulas & code management:

  - We do not like formulas served with gitfs as it may not be resilient
    to network problems and also consume more network resources.
  - For thus, we do prior checkouts and then we have a local checkout
    of the formula repository, and we then must link the inner formula
    subfolder inside our salt states tree root.

That's why you will maybe add to core repositories new formulaes by
modyfing the confRepos keys as follow

.. code-block:: yaml

    salt:
     common:
      confRepos:
        <id>:
          name: git url of the repo
          target: path on the filesystem
          link: (optionnal and mainly useful for formulaes)
            name: target path name on the fs
            target: absolute path of the symlink
    salt:
     common:
      confRepos:
        docker-formulae:
          name: https://github.com/saltstack-formulas/docker-formula.git
          target: '{salt_root}/formulas/docker'
          link:
            name: '{salt_root}/docker'
            target: '{salt_root}/formulas/docker/docker'



