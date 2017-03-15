Nodejs configuration
=====================
Install Node.js and allow the installation of Node.js packages through npm.

You can use the grain/pillar following setting to select the npm packages:

Exposed settings:

    :makina-states.localsettings.npm.packages: LIST (default: [])
    :makina-states.localsettings.npm.versions: LIST (default: [])

You can include version for packages, eg::

    makina-states.localsettings.npm.packages: ['grunt@0.6']

There is a macro available to specify the version of node.js you want to use.
Be sure to have them installed first::

    makina-states.localsettings.npm.versions: ['0.8.26']

You can then use the macro::

    {% import "makina-states/localsettings/nodejs-standalone.sls" as nodejs with context %}
    {{ nodejs.npmInstall('less', '0.8.26') }}


