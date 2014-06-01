Formulaes
==========

A formulae is a set of states to install and configure a particular subset of a machine, from provision, to setup the editors up to configure an httpd server.
All formulaes containing states to deliver your applications and services follow the same organisation rules that we previously have seen in registries: controllers, nodetypes, localsettings and settings.
Examples:

    - makina-states.controllers.salt_master
    - makina-states.localsettings.vim
    - makina-states.nodetypes.dockercontainer
    - makina-states.services.http.apache

Inside those states files, the idea is to use macros as wrappers to the underlying registries shared via salt executtion modules. See the base macros bellow.

