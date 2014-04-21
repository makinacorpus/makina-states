SNMPD configuration
====================

we provide only snmpv3 configuration and totally disable snmpv2 for security
considerations.

.. _Circus: http://snmpd.readthedocs.org/en/latest/

Exposed Hooks:
    - snmpd-pre-install
    - snmpd-post-install
    - snmpd-pre-configuration
    - snmpd-post-configuration
    - snmpd-pre-restart
    - snmpd-post-restart

Pillar value start with **makina-states.services.monitoring.snmpd**.

see :ref:`mc_module_snmpd`_ for configuration options.
