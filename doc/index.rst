.. Makina States documentation master file, created by
   sphinx-quickstart on Wed Feb 12 00:59:39 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Makina States's documentation!
=========================================
Makina-States is a consistent collection of saltstack states and a cloud controller.
Please note that the documentation is far from complete, more over on the usage front.
Please have more a look on the reference chapters.

Usage
-----------

.. toctree::
   :maxdepth: 2

   usage_index.rst


Reference
-----------

.. toctree::
   :maxdepth: 2

   ref_index.rst


.. for readthedoc menu !
.. toctree::
   :maxdepth: 20
   :hidden:

   ref_design/formulaes.rst
   ref_design/hooks.rst
   ref_design/layout.rst
   ref_design/macros.rst
   ref_design/modes.rst
   ref_design/organization.rst
   ref_design/registries.rst
   ref_formulaes/cloud/generic.rst
   ref_formulaes/cloud/lxc.rst
   ref_formulaes/cloud/saltify.rst
   ref_formulaes/cloud/usage.rst
   ref_formulaes/controllers/mastersalt-hooks.rst
   ref_formulaes/controllers/mastersalt.rst
   ref_formulaes/controllers/salt-hooks.rst
   ref_formulaes/controllers/salt.rst
   ref_formulaes/localsettings/casperjs.rst
   ref_formulaes/localsettings/etckeeper.rst
   ref_formulaes/localsettings/git.rst
   ref_formulaes/localsettings/hosts.rst
   ref_formulaes/localsettings/jdk.rst
   ref_formulaes/localsettings/ldap.rst
   ref_formulaes/localsettings/locales.rst
   ref_formulaes/localsettings/localrc.rst
   ref_formulaes/localsettings/network.rst
   ref_formulaes/localsettings/nodejs.rst
   ref_formulaes/localsettings/nscd.rst
   ref_formulaes/localsettings/phantomjs.rst
   ref_formulaes/localsettings/pkgmgr.rst
   ref_formulaes/localsettings/pkgs.rst
   ref_formulaes/localsettings/python.rst
   ref_formulaes/localsettings/repository_dotdeb.rst
   ref_formulaes/localsettings/rvm.rst
   ref_formulaes/localsettings/screen.rst
   ref_formulaes/localsettings/shell.rst
   ref_formulaes/localsettings/sudo.rst
   ref_formulaes/localsettings/sysctl.rst
   ref_formulaes/localsettings/timezone.rst
   ref_formulaes/localsettings/updatedb.rst
   ref_formulaes/localsettings/users.rst
   ref_formulaes/localsettings/vim.rst
   ref_formulaes/nodetypes/devhost.rst
   ref_formulaes/nodetypes/dockercontainer.rst
   ref_formulaes/nodetypes/lxccontainer.rst
   ref_formulaes/nodetypes/server.rst
   ref_formulaes/nodetypes/travis.rst
   ref_formulaes/nodetypes/vagrantvm.rst
   ref_formulaes/nodetypes/vm.rst
   ref_formulaes/projects/apache.rst
   ref_formulaes/projects/base.rst
   ref_formulaes/projects/beecollab.rst
   ref_formulaes/projects/hooks.rst
   ref_formulaes/projects/lizmap.rst
   ref_formulaes/projects/modphp.rst
   ref_formulaes/projects/ode_api.rst
   ref_formulaes/projects/ode_frontend.rst
   ref_formulaes/projects/phpfpm.rst
   ref_formulaes/projects/python.rst
   ref_formulaes/projects/rvmapp.rst
   ref_formulaes/projects/zope.rst
   ref_macros/apache.rst
   ref_macros/bootstraps.rst
   ref_macros/circus.rst
   ref_macros/controllers.rst
   ref_macros/funcs.rst
   ref_macros/index.rst
   ref_macros/localsettings.rst
   ref_macros/nodetypes.rst
   ref_macros/php.rst
   ref_macros/salt.rst
   ref_macros/services.rst
   ref_states/api/saltapi.rst
   ref_states/api/utils.rst
   ref_states/grains/makina_grains.rst
   ref_states/modules/mc_apache.rst
   ref_states/modules/mc_autoupgrade.rst
   ref_states/modules/mc_bind.rst
   ref_states/modules/mc_bootstraps.rst
   ref_states/modules/mc_burp.rst
   ref_states/modules/mc_casperjs.rst
   ref_states/modules/mc_circus.rst
   ref_states/modules/mc_cloud_compute_node.rst
   ref_states/modules/mc_cloud_controller.rst
   ref_states/modules/mc_cloud_images.rst
   ref_states/modules/mc_cloud_lxc.rst
   ref_states/modules/mc_cloud.rst
   ref_states/modules/mc_cloud_saltify.rst
   ref_states/modules/mc_controllers.rst
   ref_states/modules/mc_dbsmartbackup.rst
   ref_states/modules/mc_dhcpd.rst
   ref_states/modules/mc_dns.rst
   ref_states/modules/mc_env.rst
   ref_states/modules/mc_etckeeper.rst
   ref_states/modules/mc_etherpad.rst
   ref_states/modules/mc_fail2ban.rst
   ref_states/modules/mc_grub.rst
   ref_states/modules/mc_haproxy.rst
   ref_states/modules/mc_icinga.rst
   ref_states/modules/mc_icinga_web.rst
   ref_states/modules/mc_java.rst
   ref_states/modules/mc_kernel.rst
   ref_states/modules/mc_locales.rst
   ref_states/modules/mc_localsettings.rst
   ref_states/modules/mc_locations.rst
   ref_states/modules/mc_logrotate.rst
   ref_states/modules/mc_lxc.rst
   ref_states/modules/mc_macros.rst
   ref_states/modules/mc_memcached.rst
   ref_states/modules/mc_mongodb.rst
   ref_states/modules/mc_mumble.rst
   ref_states/modules/mc_mysql.rst
   ref_states/modules/mc_nagvis.rst
   ref_states/modules/mc_network.rst
   ref_states/modules/mc_nginx.rst
   ref_states/modules/mc_nodejs.rst
   ref_states/modules/mc_nodetypes.rst
   ref_states/modules/mc_ntp.rst
   ref_states/modules/mc_pgsql.rst
   ref_states/modules/mc_phantomjs.rst
   ref_states/modules/mc_php.rst
   ref_states/modules/mc_pkgs.rst
   ref_states/modules/mc_pnp4nagios.rst
   ref_states/modules/mc_postfix.rst
   ref_states/modules/mc_project_2.rst
   ref_states/modules/mc_project.rst
   ref_states/modules/mc_provider.rst
   ref_states/modules/mc_psad.rst
   ref_states/modules/mc_pureftpd.rst
   ref_states/modules/mc_python.rst
   ref_states/modules/mc_rabbitmq.rst
   ref_states/modules/mc_rdiffbackup.rst
   ref_states/modules/mc_redis.rst
   ref_states/modules/mc_remote.rst
   ref_states/modules/mc_rsyslog.rst
   ref_states/modules/mc_rvm.rst
   ref_states/modules/mc_salt.rst
   ref_states/modules/mc_screen.rst
   ref_states/modules/mc_services.rst
   ref_states/modules/mc_shorewall.rst
   ref_states/modules/mc_snmpd.rst
   ref_states/modules/mc_ssh.rst
   ref_states/modules/mc_ssl.rst
   ref_states/modules/mc_supervisor.rst
   ref_states/modules/mc_timezone.rst
   ref_states/modules/mc_tomcat.rst
   ref_states/modules/mc_ulogd.rst
   ref_states/modules/mc_updatedb.rst
   ref_states/modules/mc_usergroup.rst
   ref_states/modules/mc_utils.rst
   ref_states/modules/mc_uwsgi.rst
   ref_states/modules/mc_www.rst
   ref_states/runners/mc_api.rst
   ref_states/runners/mc_cloud_compute_node.rst
   ref_states/runners/mc_cloud_controller.rst
   ref_states/runners/mc_cloud_lxc.rst
   ref_states/runners/mc_cloud_vm.rst
   ref_states/runners/mc_lxc.rst
   ref_states/states/bacula.rst
   ref_states/states/mc_apache.rst
   ref_states/states/mc_git.rst
   ref_states/states/mc_postgres_database.rst
   ref_states/states/mc_postgres_extension.rst
   ref_states/states/mc_postgres_group.rst
   ref_states/states/mc_postgres_user.rst
   ref_states/states/mc_proxy.rst
   ref_states/states/mc_registry.rst 
   usage_general/about.rst
   usage_general/configure.rst
   usage_general/install.rst
   usage_lxc/firewalls.rst
   usage_lxc/install_template.rst
   usage_mastersalt/install_mastersalt.rst
   usage_misc/activate_forwarding.rst
   usage_misc/DEBIAN_LENNY.rst
   usage_misc/troubleshooting.rst
   usage_quickstart/install_systemd.rst
   usage_quickstart/install_ubuntu.rst
   usage_write/service.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

