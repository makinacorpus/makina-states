Salt
===============

To configure all salt daemons including at least a minion and certainly a master, we have three states files

    :`salt`_: install the base salt filesystem layout and files
    :`salt_master`_: configure a salt master daemon
    :`salt_minion`_: configure a salt minion daemon

Many of the makina-states components can select a branch (see mc_salt.settings module)
Eg for makina-states::

    makina-states.salt.makina-states.rev: apiv2

All those states files have a **-standalone** variant that let us redo a light reconfiguration upon highstates to take less time but with enought configuration to let us assume that the installation is sufficiently correct.

All those formulaes are thin wrappers to the `salt_macro`_.

.. _`controllers`: https://github.com/makinacorpus/makina-states/tree/master/controllers
.. _`salt`: https://github.com/makinacorpus/makina-states/tree/master/controllers/salt.sls
.. _`salt_master`: https://github.com/makinacorpus/makina-states/tree/master/controllers/salt_master.sls
.. _`salt_minion`: https://github.com/makinacorpus/makina-states/tree/master/controllers/salt_minion.sls
.. _`salt_macro`: https://github.com/makinacorpus/makina-states/blob/master/_macros/salt.jinja



