About
=====
Makina-States is:

    - a consistent collection of SaltStack_ formulaes
    - shell scripts
    - A buildout_ to install salt according to makina-states layout

This aim to manage easily an IT infrastructure from machine provision to project deployment & lifecycle.

It may be separated into two parts called **mastersalt** and **salt** but this is totally optionnal and up to you.

Here is how we separate things bewteen the two daemons:

    - **the infrastructure tasks**

        - making a machine up & running
        - installing the base configuration upon
        - the firewall configuration.
        - etc

    - **the projects tasks**

        - installing consumed services like a reverse proxy, a database server
        - installing the application
        - isntall project maintainance related stuff like restarts crons, databases backups
        - etc

The first goal of this project is to manage a machine lifecyle using SaltStack_
The subsidiary goal is to make those bunch of states a base to create a PaaS project to deploy and configure using salt and ultimatlely on baremetal machines where all services will run on docker_ containers.

Here salt will be use:

    - To maintain the baremetal boxes
    - To maintain containers
    - To orchestrate, recycle & scale docker_ containers
    - To provision the initial containers setup before they go as a base image

.. _SaltStack: http://www.saltstack.com/
.. _docker: http://docker.io
.. _buildout: http://en.wikipedia.org/wiki/Buildout
