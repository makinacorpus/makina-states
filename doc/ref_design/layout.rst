Base Filesystem Layout
=======================
Please respect the following layout when you write states

Salt
----
    - **/salt-venv**: salt virtualenv
    - **/srv/salt**: salt file root
    - **/srv/salt/makina-states**: makina-states clone
    - **/srv/pillar**: Pillar
    - **/var/log/salt**: log files
    - **/var/cache/salt**: salt cache files
    - **/var/run/salt**: salt run files
    - **/etc/salt**: salt configuration files
    - **/etc/makina-states/branch**: current used makina-states branch
    - **/etc/makina-states/nodetype**: configuration of the current nodetype
    - **/etc/salt/makina-states**: local registries

Mastersalt mode
---------------
    - **/mastersalt-venv**: mastersalt virtualenv
    - **/srv/mastersalt**: mastersalt file root
    - **/srv/mastersalt/makina-states**: makina-states clone
    - **/srv/mastersalt-pillar**: Pillar
    - **/var/log/mastersalt**: log files
    - **/var/cache/mastersalt**: mastersalt cache files
    - **/var/run/mastersalt**: mastersalt run files
    - **/etc/mastersalt**: mastersalt configuration files
    - **/etc/mastersalt/makina-states**: local registries

Misc locations
--------------
    - **/srv/apps**: Third party & non system packaged application
    - **/srv/backups**: root for file based backups or database dumps

Projects integration
---------------------
    - **/srv/projects/<project_name>/salt**:
    - **/srv/projects/<project_name>/pillar**:
    - **/srv/projects/<project_name>/project**:
    - **/srv/pillar/makina-projects/<project_name>/salt**: Symlink to the pillar project directory
    - **/srv/salt/makina-projects/<project_name>/salt**: Symlink to the salt project directory



