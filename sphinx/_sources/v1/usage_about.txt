About
=====
Makina-States is:

    - a consistent collection of SaltStack_ formulaes and salt modules
      (execution, states, grains, runners, etc)
    - a consistent way to deploy various projects with salt
    - a collection of shell scripts

The idea is to have a coherent provision and orchestration lifecycle, leveraging saltstack for the implementation:

    - Infrastructure will be orchestrated via makina-states
    - Projects will be delivered as docker containers prebacked via salt
    - A clear separation of concerns with the sysadmin stuff of the developper
      stuff has to be done whenever possible to hide uneccessary complexity.

This is why we have two parts called **mastersalt** and **salt** but this is totally optionnal and up to you
to use them separatly (default) or in a mixed mode:

    - **the infrastructure tasks** called **mastersalt** (/srv/mastersalt)

        - making a machine up & running
        - installing the base configuration upon
        - configuring the firewall
        - etc

    - **the projects tasks** called **salt** (/srv/salt)

        - installing consumed services like a reverse proxy, a database server
        - installing the application
        - install project maintainance related stuff like restart crons, or databases backups
        - etc

.. _SaltStack: http://www.saltstack.com/
.. _docker: http://docker.io
.. _buildout: http://en.wikipedia.org/wiki/Buildout
