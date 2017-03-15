---
title: Services
tags: [reference, installation]
weight: 4000
menu:
  main:
    parent: reference
    identifier: reference_services
---

- Salt States dedicated to install services on the targeted environment

## States
- [services States](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services)
- non exhaustive shortcuts:

### backup
| State | State |
|-------|-------|
| [services/backup/bacula](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/backup/bacula) | [services/backup/dbsmartbackup](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/backup/dbsmartbackup)     |
| [services/backup/burp](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/backup/burp)     | [services/backup/rdiff-backup](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/backup/rdiff-backup)       |


### base
| State | State |
|-------|-------|
| [services/base/cron](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/base/cron) | [services/base/ntp](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/base/ntp)                 |
| [services/base/dbus](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/base/dbus) | [services/base/ssh](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/base/ssh)                 |
                                                                                                                    | [services/cache/memcached](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/cache/memcached)   |


### misc
| State | State |
|-------|-------|
| [services/collab/etherpad](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/collab/etherpad)  | [services/queue/rabbitmq](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/queue/rabbitmq)                 |
| [services/sound/mumble](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/sound/mumble)        | [services/ftp/pureftpd](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/ftp/pureftpd) |


### db
| State | State |
|-------|-------|
| [services/db/mongodb](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/db/mongodb) | [services/db/postgresql](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/db/postgresql)                   |
| [services/db/mysql](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/db/mysql)     | [services/db/redis](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/db/redis)                             |


### dns
| State | State |
|-------|-------|
| [services/dns/dhcpd](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/dns/dhcpd) |  [services/dns/slapd](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/dns/slapd) |
| [services/dns/bind](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/dns/bind)  |


### firewall
| State | State |
|-------|-------|
| [services/firewall/shorewall](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/firewall/shorewall)  | [services/firewall/firewalld](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/firewall/firewalld)         |
| [services/firewall/firewall](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/firewall/firewall)    | [services/firewall/ms_iptables](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/firewall/ms_iptables)     |
| [services/firewall/fail2ban](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/firewall/fail2ban)    | [services/firewall/psad](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/firewall/psad)                   |


### gis
| State |
|-------|
| [services/gis/postgis](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/gis/postgis)    | [services/gis/qgis](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/gis/qgis)                             |
| [services/gis/ubuntugis](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/gis/ubuntugis)  |


### http
| State | State |
|-------|-------|
| [services/http/nginx](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/http/nginx)   | [services/http/apache_modfastcgi](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/http/apache_modfastcgi) |
| [services/http/apache](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/http/apache) | [services/http/apache_modfcgid](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/http/apache_modfcgid)     |
| [services/java/tomcat](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/java/tomcat) | [services/http/apache_modproxy](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/http/apache_modproxy)     |


### log
| State | State |
|-------|-------|
| [services/log/rsyslog](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/log/rsyslog)         | [services/log/ulogd](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/log/ulogd)                           |  |


### Mail
| State | State |
|-------|-------|
| [services/mail/dovecot](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/mail/dovecot)                     | [services/mail/postfix](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/mail/postfix)                     |


### Monitoring
| State | State |
|-------|-------|
| [services/monitoring/client](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/monitoring/client)           | [services/monitoring/icinga_web2](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/monitoring/icinga_web2) |
| [services/monitoring/icinga](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/monitoring/icinga)           | [services/monitoring/nagvis](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/monitoring/nagvis)           |
| [services/monitoring/icinga2](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/monitoring/icinga2)         | [services/monitoring/pnp4nagios](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/monitoring/pnp4nagios)   |
| [services/monitoring/icinga_web](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/monitoring/icinga_web)   | [services/monitoring/snmpd](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/monitoring/snmpd)             |

### php
| State | State |
|-------|-------|
| [services/php/common](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/php/common)                         | [services/php/modphp](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/php/modphp)                         |
| [services/php/phpfpm](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/php/phpfpm)                         | [services/php/phpfpm_with_apache](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/php/phpfpm_with_apache) |
| [services/php/phpfpm_with_nginx](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/php/phpfpm_with_nginx)   | |


### Proxy
| State | State |
|-------|-------|
| [services/proxy/haproxy](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/proxy/haproxy)  | [services/proxy/uwsgi](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/proxy/uwsgi)                       |  |


### virt
| State | State |
|-------|-------|
| [services/virt/docker](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/virt/docker)     | [services/virt/kvm](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/virt/kvm)                             |
| [services/virt/lxc](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/virt/lxc)           | [services/virt/virtualbox](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/services/virt/virtualbox)               |
