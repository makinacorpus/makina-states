Icinga configuration
====================

See :ref:`module_mc_icinga` for configuration options.

The icinga module can provide:

  - configuration of icinga core
  - configuration of database for ido2db
  - configuration of ido2db daemon
  - configuration of uwsgi in order to serve cgi
  - configuration of nginx to serve cgi throug uwsgi


The icinga_web module can provide:

  - configuration of icinga web
  - configuration of database for icinga web
  - configuration of php-fpm
  - configuration of nginx to serve php webpages throug php-fpm

icinga_web module can configure its nginx virtualhost to serve cgi but icinga_web module doesn't configure uwsgi and doesn't install any file related to cgi.

The reason is to keep icinga and icinga_web independants. 
Icinga-web can be installed on an other host than icinga-core but CGI files require to have icinga-core installed on the host.

