Pnp4nagios configuration
========================

See :ref:`module_mc_pnp4nagios` for configuration options.


This service configure pnp4nagios with a connection to icinga 

Pnp4nagios depends on Icinga. The installation of pnp4nagios will trigger the installation of icinga.
It seems not possible to have a pnp4nagios on a different host that icinga. (you can always use a shared filesystem...)

Pnp4nagios edits icinga.cfg file in order to enable performance data.

Integration with icinga-web is done in icinga_web service.



