Write a new makina-state service
================================

For the example we are writing a new module for snmp


Integration of service needs:

    - A salt execution module to store special service parameters and configuration
    - An entry in mc_services.py:registry method to autoinstall it when needed
    - A line incorporating the module parameters in mc_services.py:settings
    - Registration of  a shortcut for accessing settings in _macros/services.jinja
    - The service formula state which must have:

        - a full mode\: 'full' named as the module is named (eg\: snmp.sls)
        - a more lightweight run mode\: 'standalone' (eg\: snmp-standalone.sls)

Taking circus as an example:

    parameters module
        https://github.com/makinacorpus/makina-states/blob/master/mc_states/modules/mc_circus.py
    service settings
        https://github.com/makinacorpus/makina-states/blob/master/mc_states/modules/mc_services.py#L111
    service autoload
        https://github.com/makinacorpus/makina-states/blob/master/mc_states/modules/mc_services.py#L198
    place for formulas
        https://github.com/makinacorpus/makina-states/tree/master/services/monitoring
    macro shortcut
        https://github.com/makinacorpus/makina-states/blob/master/_macros/services.jinja#L51
    full formula
        https://github.com/makinacorpus/makina-states/blob/master/services/monitoring/circus.sls
    standalone formula
        https://github.com/makinacorpus/makina-states/blob/master/services/monitoring/circus-standalone.sls

