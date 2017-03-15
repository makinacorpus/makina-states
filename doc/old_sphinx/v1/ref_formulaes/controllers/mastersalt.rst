MasterSalt
==========

To configure all mastersalt daemons including at least a minion and certainly a master, we have three states files

    :`mastersalt`_: install the base mastersalt filesystem layout and files
    :`mastersalt_master`_: configure a mastersalt master daemon
    :`mastersalt_minion`_: configure a mastersalt minion daemon

All those states files have a **-standalone** variant that let us redo a light reconfiguration upon highstates to take less time but with enought configuration to let us assume that the installation is sufficiently correct.

All those formulaes are thin wrappers to the `salt_macro`_.

.. _`controllers`: https://github.com/makinacorpus/makina-states/tree/master/controllers
.. _`mastersalt`: https://github.com/makinacorpus/makina-states/tree/master/controllers/salt.sls
.. _`mastersalt_master`: https://github.com/makinacorpus/makina-states/tree/master/controllers/salt_master.sls
.. _`mastersalt_minion`: https://github.com/makinacorpus/makina-states/tree/master/controllers/salt_minion.sls
.. _`salt_macro`: https://github.com/makinacorpus/makina-states/blob/master/_macros/salt.jinja



