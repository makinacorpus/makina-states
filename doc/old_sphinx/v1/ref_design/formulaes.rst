Formulaes
==========

A formulae is a set of states to install and configure a particular subset of a machine,
from provision, to setup the editors up to configure an httpd server.
All formulaes containing states to deliver your applications and services
follow the same organisation rules that we previously have seen in registries:

    - nodetypes: preset for a type of machine
    - controllers: salt/mastersalt
    - localsettings: base conf (network, editors, languages, compilators, etc)
    - services: databases, servers (sshd), etc.

Examples:

    - makina-states.nodetypes.dockercontainer
    - makina-states.controllers.salt_master
    - makina-states.localsettings.vim
    - makina-states.localsettings.python
    - makina-states.services.http.apache
    - makina-states.services.http.nginx
    - makina-states.services.base.openssh.server
    - makina-states.services.proxy.haproxy

Inside those states files, the idea is to configure the states via the
underlying registries shared via salt executtion modules.

