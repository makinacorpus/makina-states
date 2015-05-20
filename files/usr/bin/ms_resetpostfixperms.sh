#!/usr/bin/env bash
set -e
for i in\
    /var/spool/postfix/active   \
    /var/spool/postfix/bounce   \
    /var/spool/postfix/corrupt  \
    /var/spool/postfix/defer    \
    /var/spool/postfix/deferred \
    /var/spool/postfix/flush    \
    /var/spool/postfix/hold     \
    /var/spool/postfix/incoming \
    /var/spool/postfix/private  \
    /var/spool/postfix/saved    \
    /var/spool/postfix/trace    \
    ;do
if [ -e "${i}" ];then
    chown postfix:root "${i}"
fi
done
for i in\
    /etc/postfix/certificate.key              \
    /etc/postfix/certificate.pub              \
    /etc/postfix/destinations                 \
    /etc/postfix/destinations.db              \
    /etc/postfix/destinations.local           \
    /etc/postfix/destinations.local.db        \
    /etc/postfix/dynamicmaps.cf               \
    /etc/postfix/main.cf                      \
    /etc/postfix/master.cf                    \
    /etc/postfix/networks                     \
    /etc/postfix/networks.db                  \
    /etc/postfix/networks.local               \
    /etc/postfix/networks.local.db            \
    /etc/postfix/postfix-files                \
    /etc/postfix/postfix-script               \
    /etc/postfix/post-install                 \
    /etc/postfix/relay_domains                \
    /etc/postfix/relay_domains.db             \
    /etc/postfix/relay_domains.local          \
    /etc/postfix/relay_domains.local.db       \
    /etc/postfix/sasl_passwd                  \
    /etc/postfix/sasl_passwd.db               \
    /etc/postfix/sasl_passwd.local            \
    /etc/postfix/sasl_passwd.local.db         \
    /etc/postfix/transport                    \
    /etc/postfix/transport.db                 \
    /etc/postfix/transport.local              \
    /etc/postfix/transport.local.db           \
    /etc/postfix/virtual_alias_maps           \
    /etc/postfix/virtual_alias_maps.db        \
    /etc/postfix/virtual_alias_maps.local     \
    /etc/postfix/virtual_alias_maps.local.db  \
    ;do
if [ -e "${i}" ];then
    chown root:postfix "${i}"
fi
done
for i in\
    /usr/sbin/postdrop  \
    /usr/sbin/postqueue \
;do
if [ -e "${i}" ];then
    chmod g-s "${i}"
    chown root:postdrop "${i}"
    chmod g+s "${i}"
fi
done
if [ -e /var/lib/postfix ];then
    chown -Rf postfix:postdrop /var/lib/postfix
fi
if [ -e /var/spool/postfix/public ];then
    chmod g-s /var/spool/postfix/public
    chown postfix:postdrop /var/spool/postfix/public
    chmod g+s /var/spool/postfix/public
fi
if [ -e /var/spool/postfix/maildrop ];then
    chown postfix:postdrop /var/spool/postfix/maildrop
fi
# vim:set et sts=4 ts=4 tw=80:
