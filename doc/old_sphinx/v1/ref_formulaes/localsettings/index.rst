Localsettings
=============
Those formulaes will configure basic configuration on your host that is/are not tied to a service

For example; writing something in /etc is a good catch for a localsettings states

We let the user have a word on the final local settings which are activated
This can be customized by putting keys either in pillar or in grains
in the form: 'makina-states.localsettings.<statename>'

EG: to disable the default vim configuration, either set a grain or a pillar value::

    makina-states.localsettings.vim: False

.. toctree::
   :maxdepth: 1

   casperjs.rst
   phantomjs.rst
   updatedb.rst
   timezone.rst
   etckeeper.rst
   git.rst
   hosts.rst
   jdk.rst
   ldap.rst
   locales.rst
   localrc.rst
   network.rst
   nodejs.rst
   nscd.rst
   pkgmgr.rst
   pkgs.rst
   python.rst
   repository_dotdeb.rst
   rvm.rst
   shell.rst
   sudo.rst
   sysctl.rst
   users.rst
   vim.rst
   screen.rst


