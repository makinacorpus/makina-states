#!/usr/bin/env bash
if [ "x${DEBUG}" != "x" ];then
    set -x
fi
DEBIAN_MAJOR=""
VER="${1:-1.3.48}"
if [ -e /etc/debian_version ];then
    DEBIAN_MAJOR="$(cut -c1 /etc/debian_version 2>/dev/null)"
fi
_BINP="makina-states/files/usr/sbin/${DEBIAN_MAJOR}/${VER}"
SALT_ROOTS="/srv/makina-states /srv/salt"
_BINS="burp bedup burp_ca vss_strip"
IPATH="${IPATH:-/srv/apps/burp}"
if [ -e $(which burp 2>/dev/null) ];then
    if [ x"$(burp -v 2>/dev/null|awk -F- '{print $2}' 2>/dev/null)" = "x$VER" ];then
        echo 'changed="no"' && exit 0
    fi
fi
for SALT_ROOT in ${SALT_ROOTS};do
    if [ -e ${SALT_ROOT}/${_BINP}/burp ];then
        SALT_ROOT="${SALT_ROOT}"
        break
    fi
done
apt-get install -y --force-yes librsync-dev libssl-dev libssl-dev libacl1-dev rsync build-essential libncurses5-dev
ret="$?"
if [ "x${ret}" != "x0" ];then
    echo "prerequisites failed" && exit 1
fi
if [ -e ${SALT_ROOT}/${_BINP}/burp ];then
    cp -fv ${SALT_ROOT}/${_BINP}/burp /usr/sbin/burp &&
    cp -fv ${SALT_ROOT}/${_BINP}/vss_strip /usr/sbin/vss_strip &&
    cp -fv ${SALT_ROOT}/${_BINP}/burp_ca /usr/sbin/burp_ca &&
    cp -fv ${SALT_ROOT}/${_BINP}/bedup /usr/sbin/bedup
    if [ "x${?}" = "x0" ];then
        echo 'changed="yes"' && exit 0
    fi
fi
build_uthash=""
configure_opts=""
if [ ! -e "${IPATH}" ];then
    mkdir -p "${IPATH}"
fi
cd "${IPATH}"
if [ -e /etc/debian_version ];then
    if [ "x$(cat /etc/debian_version 2>/dev/null)" = "x5.0.3" ];then
        PATH="/var/makina/minitage/dependencies/git-1.7/parts/part/bin:$PATH"
    fi &&\
    if [ "x${DEBIAN_MAJOR}" != "x" ];then
        if [ $DEBIAN_MAJOR  -lt 6 ];then
            echo "disabling acl && manually install utash!" &&\
            build_uthash="y" &&\
            configure_opts="$configure_opts --disable-acl"
        fi
    fi
fi
wget -c https://github.com/grke/burp/archive/${VER}.tar.gz -O ${VER}.tar.gz
if [ ! -e burp-$VER/README ];then
    rm -rf burp-$VER
    tar xzvf ${VER}.tar.gz
    #git clone https://github.com/grke/burp.git
fi &&\
cd burp-${VER} && \
if [ "x$build_uthash" != "x" ];then
    if [ "x$(dpkg -l uthash-dev|grep "1.9.7-1"|wc -l|sed -e "s/ //g")" = "x0" ];then
        wget http://ftp.us.debian.org/debian/pool/main/u/uthash/uthash-dev_1.9.7-1_all.deb &&\
        dpkg -i uthash-dev_1.9.7-1_all.deb
    fi
else
   apt-get install uthash-dev
fi &&\
./configure $configure_opts && make && make install && echo 'changed="yes"'
ret=$?
if [ "x$ret" != "x0" ];then
    exit $ret
fi
#git fetch --all &&\
#git reset --hard "remotes/origin/${VER}" &&\
