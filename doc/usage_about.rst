About
=====


Idea is to have all the provision and orchestration done with saltstack:

    - Servers will be orchestrated via makina-states
    - Projects will be delivered as docker containers prebacked via salt

For now Makina-States is:

    - a consistent collection of SaltStack_ formulaes
    - a consistent way to deploy numerous projects with salt
    - shell scripts

This aim to manage and orchestrate easily an IT infrastructure from machine provision to project deployment & lifecycle.
The other aim is to make this infrastructure deploy to any PAAS platform.

It may be separated into two parts called **mastersalt** and **salt** but this is totally optionnal and up to you.

Here is how we separate things between the two xenvironments

    - **the infrastructure tasks** called mastersalt (/srv/mastersalt)

        - making a machine up & running
        - installing the base configuration upon
        - the firewall configuration.
        - etc

    - **the projects tasks** called salt (/srv/salt)

        - installing consumed services like a reverse proxy, a database server
        - installing the application
        - isntall project maintainance related stuff like restarts crons, databases backups
        - etc

.. _SaltStack: http://www.saltstack.com/
.. _docker: http://docker.io
.. _buildout: http://en.wikipedia.org/wiki/Buildout
