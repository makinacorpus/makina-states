{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set icingaSettings = salt['mc_icinga.settings']() %}
include:
  - makina-states.services.monitoring.icinga.hooks

icinga-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      {% for package in icingaSettings.package %}
      - {{package}}
      {% endfor %}

{% if icingaSettings.modules.ido2db.enabled %}
icinga-ido2db-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      {% for package in icingaSettings.modules.ido2db.package %}
      - {{package}}
      {% endfor %}
{% endif %}

{% if icingaSettings.modules.cgi.enabled %}
icinga-cgi-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      {% for package in icingaSettings.modules.cgi.package %}
      - {{package}}
      {% endfor %}
{% endif %}

{% if icingaSettings.modules['nagios-plugins'].enabled %}
icinga-nagios-plugins-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      {% for package in icingaSettings.modules['nagios-plugins'].package %}
      - {{package}}
      {% endfor %}
{% endif %}

{% if icingaSettings.modules['mklivestatus'].enabled %}
{% set tmpf = "/tmp/mk-livestatus" %}

icinga-mklivestatus-download:
  archive.extracted:
    - name: {{tmpf}}
    - source: {{icingaSettings.modules.mklivestatus.download.url}}
    - source_hash: sha512={{icingaSettings.modules.mklivestatus.download.sha512sum}}
    - archive_format: tar
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
    - watch_in:
      - mc_proxy: icinga-post-install
      - cmd: icinga-mklivestatus-build-configure
    - unless: "test -f {{icingaSettings.modules.mklivestatus.lib_file}}"

icinga-mklivestatus-build-configure:
  cmd.run:
    - name: if [[ -d "{{tmpf}}/mk-livestatus-1.2.4" ]]; then cd "{{tmpf}}/mk-livestatus-1.2.4" && ./configure --prefix=/usr/share/icinga --exec-prefix=/usr/share/icinga; fi
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
      - archive: icinga-mklivestatus-download
    - watch_in:
      - mc_proxy: icinga-post-install
      - cmd: icinga-mklivestatus-build-make

icinga-mklivestatus-build-make:
  cmd.run:
    - name: if [[ -d "{{tmpf}}/mk-livestatus-1.2.4" ]]; then cd "{{tmpf}}/mk-livestatus-1.2.4" && make; fi
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
      - cmd: icinga-mklivestatus-build-configure
    - watch_in:
      - mc_proxy: icinga-post-install

icinga-mklivestatus-install:
  file.copy:
    - name: {{icingaSettings.modules.mklivestatus.lib_file}}
    - source: {{tmpf}}/mk-livestatus-1.2.4/src/livestatus.o
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
      - cmd: icinga-mklivestatus-build-make
    - watch_in:
      - mc_proxy: icinga-post-install
    - unless: "test -f {{icingaSettings.modules.mklivestatus.lib_file}}"

icinga-mklivestatus-clean-tmp:
  file.absent:
    - name: {{tmpf}}
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
      - file: icinga-mklivestatus-install
    - watch_in:
      - mc_proxy: icinga-post-install


{% endif %}
