Zope Generic Portal install helper
===================================
This permit to install generic portals (generated via `cgwb <http://cgwb-makinacorpus.rhcloud.com/>`_ to be installed via makina states

Some nuances:

    - We generate the 'etc/sys/settings-local.cfg' file from defaults settings found in configuration or pillar, see zope defaults
    - We generate a special buildout file 'buildout-salt.cfg' file which extends the production one minus some parts that salt do itself
    - We wire the vhost produced by generic buildout and do not use makina-states apache macro for that
    - We wire the logrotate slug produced by generic buildout.
    - We wire the supervisord init script by generic buildout and register that as a service.
    - We use our own crons for zope maintainance


