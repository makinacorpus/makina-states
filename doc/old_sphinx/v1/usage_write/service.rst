Write a new makina-state service
================================

We will take the circus implementation as exemple.

Integration of service needs:

    - A :ref:`salt execution module <ref_registries>` to store special service parameters and configuration
    - An entry in mc_services.py:registry method to autoinstall it when needed
    - A line incorporating the module parameters in mc_services.py:settings

Taking circus as an example:

    - `service settings <https://github.com/makinacorpus/makina-states/blob/master/mc_states/modules/mc_circus.py>`_
    - `service autoload <https://github.com/makinacorpus/makina-states/blob/master/mc_states/modules/mc_services.py#L198>`_
    - `place for formula states <https://github.com/makinacorpus/makina-states/tree/master/services/monitoring>`_



