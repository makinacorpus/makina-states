ubuntu log to package and get PPA for a package
===============================================
Configure sources if not already done
--------------------------------------
::

    deb     http://mirror.ovh.net/ubuntu/ trusty main restricted universe
    multiverse
    deb-src http://mirror.ovh.net/ubuntu/ trusty main restricted
    deb     http://mirror.ovh.net/ubuntu/ trusty-updates main restricted
    universe multiverse
    deb     http://security.ubuntu.com/ubuntu trusty-security main restricted
    universe multiverse


Add debian developper packages
----------------------------------
::

  apt-get install -y bzr git devscripts bzr-builddeb pbuilder ubuntu-dev-tools distro-info-data

configure /etc/pbuilderrc MIRRORSITE to use::

    http://mirror.ovh.net/ubuntu/

Init
----------
::

    cd && mkdir pkg && cd pkg

Patch package
----------------
get source::

    bzr branch lp:~ubuntu-branches/ubuntu/trusty/net-snmp/trusty/ snmp

do appropriate modifications::

    vim snmp/$WTF

add new version::

    dch -v 5.7.2~dfsg-8.1ubuntu4

commit::

    bzr whoami "Mathieu Le Marec - Pasquet <kiorky@cryptelium.net>"
    bzr commit -m  "Add missing net-snmp-create-v3-user"

Build source & bin
------------------
::

    apt-get builddep snmpd
    bzr builddeb
    bzr builddeb -- -S -sa


Upload
-------
~/.dput.cfg::

    [snmp]
    fqdn = ppa.launchpad.net
    method = sftp
    incoming = ~makinacorpus/snmp/ubuntu/
    login = kiorky
    allow_unsigned_uploads = 0

::

    dput snmp net-snmp_5.7.2~dfsg-8.1ubuntu4_source.changes



