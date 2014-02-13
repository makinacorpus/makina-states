Nodejs configuration
=====================
Install Node.js and allow the installation of Node.js packages through npm.

You can use the grain/pillar following setting to select the npm packages:

Exposed settings:

    :makina-states.localsettings.npm.packages: LIST (default: [])

You can include version, eg::

    makina-states.localsettings.npm.packages: ['grunt@0.6']


