#
# nodejs configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/nodejs.rst
#}
{% set pkgsettings = salt['mc_pkgs.settings']()%}
{% set locs = salt['mc_locations.settings']()%}
{% set settings = salt['mc_nodejs.settings']()%}
include:
  - makina-states.localsettings.nodejs.hooks
{%  if grains['os'] in ['Ubuntu'] -%}
{#- NODEJS didnt land in LTS, so use the ppa
# https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager#ubuntu-mint-elementary-os
# We also install the official binaries inside /srv/app/nodejs/<ver>
#}
nodejs-repo-old:
  file.absent:
    - names:
      - "{{locs.conf_dir}}/apt/sources.list.d/nodejs.list"
      - "{{locs.conf_dir}}/apt/sources.list.d/nodejsn.list"
      - "{{locs.conf_dir}}/apt/sources.list.d/nodejs_a.list"
      - "{{locs.conf_dir}}/apt/sources.list.d/nodejs_b.list"
    - watch_in:
      - mc_proxy: nodejs-post-system-install
nodejs-repo:
  file.absent:
    - name: {{locs.conf_dir}}/apt/sources.list.d/nodejs_c.list
    - onlyif: |
              set -e
              test -e {{locs.conf_dir}}/apt/sources.list.d/nodejs_c.list
              grep -qv '{{settings.repo}} ' {{locs.conf_dir}}/apt/sources.list.d/nodejs_c.list
    - watch:
      - file: nodejs-repo-old
      - mc_proxy: nodejs-pre-system-install
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - name: nodejs
    - humanname: Node.js PPA
    - name: deb https://deb.nodesource.com/{{settings.repo}} {{pkgsettings.dist}} main
    - dist: {{pkgsettings.dist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/nodejs_c.list
    - key_url: "http://deb.nodesource.com/gpgkey/nodesource.gpg.key"
    - watch:
      - file: nodejs-repo
      - mc_proxy: nodejs-pre-system-install
{% endif %}
nodejs-pkgs-prereqs:
  pkg.{{pkgsettings['installmode']}}:
    - watch:
      - mc_proxy: nodejs-pre-system-install
    - watch_in:
      - mc_proxy: nodejs-post-system-install
    - pkgs:
      - wget
      - curl
nodejs-pkgs:
  pkg.latest:
    - watch:
      - pkg: nodejs-pkgs-prereqs
      - mc_proxy: nodejs-pre-system-install
      {% if grains['os'] in ['Ubuntu'] %}
      - pkgrepo: nodejs-repo
      {% endif %}
    - watch_in:
      - mc_proxy: nodejs-post-system-install
    - pkgs:
      - nodejs

node-js-install-yarn:
  cmd.run:
    - onlyif: {% if settings.yarn_install %}true{%else%}false{%endif %}
    - shell: /bin/bash
    - watch:
      - pkg: nodejs-pkgs
      - mc_proxy: nodejs-pre-system-install
    - watch_in:
      - mc_proxy: nodejs-post-system-install
    - name: |
        export YARN_VERSION=${YARN_VERSION:-{{settings.yarn_version}}}
        export YARN_ARCHIVE=yarn-v$YARN_VERSION.tar.gz
        export KEYSERVER=${KEYSERVER:-keyserver.ubuntu.com}
        export APP_PATH=${APP_PATH:-/usr/local}
        vv () { echo "$@">&2; "${@}"; }
        die_in_error_() { if [ "x${1-$?}" != "x0" ];then echo "FAILED: $@">&2; exit 1; fi }
        die_in_error() { die_in_error_ $? $@; }
        jv() { gpg -q --batch --verify $YARN_ARCHIVE.asc $YARN_ARCHIVE 2>/dev/null; }
        if [ ! -e ${APP_PATH} ];then mkdir -p ${APP_PATH};fi
        cd $APP_PATH
        die_in_error no $APP_PATH
        keys="{{' '.join(settings.gpg)}}"
        gpg -q --keyserver "$KEYSERVER" --recv-keys "$keys" 2>/dev/null
        die_in_error gpg keys
        if ! jv;then
            vv curl -fSL -O \
                "https://yarnpkg.com/downloads/$YARN_VERSION/$YARN_ARCHIVE.asc" &&\
            vv curl -fSL -O "https://yarnpkg.com/downloads/$YARN_VERSION/$YARN_ARCHIVE"
            die_in_error yarn download
        fi
        jv
        die_in_error yarn integrity
        tar -xzf "$YARN_ARCHIVE" --strip-components=1
        die_in_error yarn unpack
        for i in "${yarn_candidate}";do
            test -f "${i}"
        done
        chmod +x "${APP_PATH}"/bin/yarn*
        ls -1 "${APP_PATH}/bin/"yarn*
  
