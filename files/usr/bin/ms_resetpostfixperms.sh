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
if [ -e /var/spool/postfix/public ];then
    chmod g-s /var/spool/postfix/public
    chown postfix:postdrop /var/spool/postfix/public
    chmod g+s /var/spool/postfix/public
fi
if [ -e /var/spool/postfix/maildrop ];then
    chown postfix:postdrop /var/spool/postfix/maildrop
fi
# vim:set et sts=4 ts=4 tw=80:
