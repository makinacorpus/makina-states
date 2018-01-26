#!/usr/bin/env bash
cd $(dirname $0)
LOGGER_NAME=${LOGGER_NAME:-docbuilder}
. ../_scripts/shell_common || exit 1
if [[ -z ${BUILD_SKIP} ]];then
    ./build.sh
    die_in_error "build failed"
fi
URL=$(git config remote.o.url || git config remote.origin.url)
if [[ -z ${PUSH_SKIP} ]];then
    cd html && \
        if [ ! -e .git ];then git init;fi &&\
        echo "makinastates.makina-corpus.com">CNAME && \
        touch .nojekyll && git add .nojekyll &&\
        git add --all -f . &&\
        ( git k || /bin/true ) &&\
        git commit -am "Publish" &&\
        git push --force $URL HEAD:refs/heads/gh-pages
    die_in_error "git pages publish"
fi

# vim:set et sts=4 ts=4 tw=80:
