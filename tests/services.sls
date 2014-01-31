include:
  - makina-states.services.backup.bacula-fd
  - makina-states.services.backup.dbsmartbackup
  - makina-states.services.backup.rdiff-backup
  - makina-states.services.backup.users
  - makina-states.services.base.ntp
  - makina-states.services.base.ssh
  - makina-states.services.db.mysql
  - makina-states.services.db.postgresql
  - makina-states.services.ftp.pureftpd
  - makina-states.services.gis.postgis
  - makina-states.services.gis.qgis
  - makina-states.services.http.apache
  - makina-states.services.http.nginx
  - makina-states.services.mail.dovecot
  - makina-states.services.mail.postfix
  - makina-states.services.virt.docker
  - makina-states.services.virt.lxc

{# TODO: make some conf to make those following states testable
  - makina-states.services.php.common
  - makina-states.services.php.modphp 
  - makina-states.services.php.phpfpm
  - makina-states.services.php.phpfpm_with_apache
  - makina-states.services.php.php_macros.jinja
  - makina-states.services.firewall.shorewall
  - makina-states.services.db.mysql_example
  - makina-states.services.java.tomcat7
  - makina-states.services.java.solr4-defaults.jinja
  - makina-states.services.java.solr4
  - makina-states.services.virt.docker-shorewall
  - makina-states.services.virt.lxc-shorewall
#}

{# XXX: not maintained anymore
  - makina-states.services.backup.astrailssafe
  - makina-states.services.openstack.openstack_controller

#}
