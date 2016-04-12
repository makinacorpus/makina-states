#!/usr/bin/env bash
# if we found the password reset flag, reset any password found
# in shadow entries back to a random value
if test -e /passwords.reset && which chpasswd >/dev/null 2>&1;then
    unflag=""
    for user in $(cat /etc/shadow | awk -F: '{print $1}');do
        oldpw=$(getent shadow ${user} | awk -F: '{print $2}')
        if [ "x${oldpw}" != "x" ] &&\
            [ "x${oldpw}" != "x*" ] &&\
            [ "x${oldpw}" != "x!" ] &&\
            [ "x${oldpw}" != "x!!" ] &&\
            [ "x${oldpw}" != "xNC" ] &&\
            [ "x${oldpw}" != "xLK" ];then
            pw=$(< /dev/urandom tr -dc A-Za-z0-9 | head -c${1:-32};echo)
            echo "Resetting password for ${user}"
            echo "${user}:${pw}" | chpasswd
            if [ "x${?}" != "x0" ];then
                unflag="n"
            fi
        fi
    done
    if [ "x${unflag}" = "x" ];then rm -f /passwords.reset || /bin/true;fi
else
    echo "/passwords.reset not found, if you really want to reset all defined user passwords, do"
    echo "touch /passwords.reset"
fi
# vim:set et sts=4 ts=4 tw=80:
