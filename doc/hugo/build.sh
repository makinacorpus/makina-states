#!/usr/bin/env bash
cd "$(dirname "${0}")"
LOGGER_NAME=${LOGGER_NAME:-hugobuilder}
. ../../_scripts/shell_common || exit 1
if [ -z ${APT_SKIP} ]; then
    vv apt-get install -y curl
    die_in_error "apt"
fi
if [ -z ${THEME_SKIP} ]; then
    if [ ! -e themes/hugo-mc-docs ];then
        git clone \
            https://github.com/makinacorpus/hugo-mc-docs.git \
            themes/hugo-mc-docs
        die_in_error "hugo theme clone"
    fi
    ( cd themes/hugo-mc-docs &&\
      git fetch origin &&\
      git stash || /bin/true &&\
      git reset --hard origin/master )
    die_in_error "hugo theme refresh"
fi
cd $W || die_in_error "no $W"
if [ -z ${INSTALL_SKIP} ]; then
    themes/hugo-mc-docs/bin/control.sh install
    die_in_error "hugo install"
fi
if [[ -z $SPHINX_SKIP ]];then
    if [[ ! -e public ]];then
        mkdir public
    fi
    if [[ -e ../sphinx/build/html ]];then
        rsync -azv --delete ../sphinx/build/html/ public/sphinx/
    fi
    die_in_error "sphinx sync"
fi
if [ -z ${BUILD_SKIP} ]; then
    themes/hugo-mc-docs/bin/control.sh ${@:-gulp}
    die_in_error "hugo gen"
fi
# vim:set et sts=4 ts=4 tw=80:
