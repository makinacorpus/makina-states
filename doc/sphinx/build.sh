#!/usr/bin/env bash
cd "$(dirname "${0}")"
LOGGER_NAME=${LOGGER_NAME:-sphinxbuilder}
. ../../_scripts/shell_common
if [ -z ${APT_SKIP} ]; then
    vv apt-get install -y libopenjpeg-dev libwebp-dev libwebp5 libtiff5-dev libtiff5 libreadline-dev libcairo2-dev
    die_in_error "apt"
fi
if [ -z ${VENV_SKIP} ]; then
    if [ ! -e venv/bin/activate ];then
        ( vv virtualenv --no-site-packages venv &&
            . venv/bin/activate &&
            vv pip install --upgrade pip)
        die_in_error "venv"
    fi
    . venv/bin/activate
    die_in_error "venv activation"
    vv pip install -r reqs.txt
    die_in_error "sphinx reqs"
else
    . venv/bin/activate
    die_in_error "venv activation"
fi

debug() {
    if  [[ -n $DEBUG ]];then
        echo $@
    fi
}

pymod() {
    echo $@|sed -re "s/.py$//" -e "s/\//./g"
}
add_sphinx_module() {
    f=$1
    k=$2
    df=$(basename $f .py).rst
    c=$(dirname $f)/$df
    dd=api/$k/$(dirname $f)
    d=$dd/$df
    pym=$(pymod $f)
    debug "Adding $pym to sphinx subsection $k: $d $dd"
    if [ ! -e $dd ];then mkdir -p $dd;fi
    cat  > $d << EOF

EOF
    printf \
        ".. automodule:: $pym\n    :members:\n\n\n" \
        >> $d
    collected="$collected $c"
}
write_section() {
    section=${1:-${session}}
    t=api/$section/index.rst
    debug "Including $collected in $t"
    if [ ! -e $section ];then
        mkdir -p $section
    fi
    cat  > $t << EOF
$section Modules
==========================================================
.. toctree::
   :maxdepth: 2

EOF
    for i in $collected;do
        echo "   $i" >> $t
    done
    echo >> $t
    echo >> $t
}

if [ -z ${DOC_SYNC_SKIP} ]; then
    vv rsync -azv --delete ../../mc_states/ mc_states/
    die_in_error "rsync reqs"
fi

rewrite_section() {
    section=""
    collected=""
    local s=$1
    local d=$2
    rm -rf api/$s
    while read f;do add_sphinx_module "$f" "$s";done < \
        <( find  ${d}/*py -type f | grep -v __init__)
    write_section $s
}


if [ -z ${REWRITE_SKIP} ]; then
    find mc_states -name *.tmp -delete
    rm -rf mc_states/tests &&\
        find mc_states -type f | while read f
    do
        grep -v 'from __future' "${f}" > "${f}.tmp" &&\
        mv -f "${f}.tmp" "${f}"
    done
    rewrite_section api mc_states
    rewrite_section modules mc_states/modules
    rewrite_section grains mc_states/grains
    rewrite_section pillars mc_states/pillar
    rewrite_section states mc_states/states
    die_in_error "rewrite docs"
fi
if [ "x${1}" != "nobuild" ];then
    make html
    die_in_error "sphinx gen"
fi
# vim:set et sts=4 ts=4 tw=80:
