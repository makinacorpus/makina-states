{% set default_os_mirrors='http://foo.com' %}
{% set default_dist='' %}
{% set default_comps='' %}
{% set default_url='' %}

{% if grains['os'] == 'Ubuntu' %}
{% set default_os_mirrors='http://archive.ubuntu.com/ubuntu' %}
{% set default_url='http://fr.archive.ubuntu.com/ubuntu' %}
{% set default_dist=grains.get('lsb_distrib_codename', 'raring') %}
{% set default_comps= 'main restricted universe multiverse' %}
{% endif %}

{% set default_os_mirrors=salt['config.get']('default_os_mirrors', default_os_mirrors) %}
{% if grains['os'] == 'Ubuntu' %}
{% set default_os_mirrors='http://archive.ubuntu.com/ubuntu|'+default_os_mirrors %}
{% endif %}
{% set comps=salt['config.get']('apt_comps', default_comps) %}
{% set mirror=salt['config.get']('apt_mirror', default_url) %}
{% set dist=salt['config.get']('apt_dist', default_dist) %}

{% macro set_packages_repos(root='', suf='', update=True) %}
# can be adapted to other debian systems, but not the time right now
# we do not use pkgrepo.managed here to avoid useless apt-get upate
# and to use it to configure inner vm or containers where what we edit
# is not the system source.list
{% if grains['os'] == 'Ubuntu' %}
{% if update %}
update-default-repos{{suf}}:
  cmd.run:
    - name: apt-get update
    - require_in:
      - file: main-repos{{suf}}
      - file: main-repos-updates{{suf}}
{% endif %}
remove-default-src-repos{{suf}}:
  file.replace:
    - name: {{root}}/etc/apt/sources.list
    - pattern: deb-src\s.*({{default_os_mirrors}}|{{mirror}}).*
    - repl: ''
    - flags: ['MULTILINE', 'DOTALL']
remove-default-repos{{suf}}:
  file.replace:
    - name: {{root}}/etc/apt/sources.list
    - pattern: deb\s.*({{default_os_mirrors}}|{{mirror}}).*
    - repl: ''
    - flags: ['MULTILINE', 'DOTALL']

main-repos{{suf}}:
  file.append:
    - name: {{root}}/etc/apt/sources.list
    - text: deb {{mirror}} {{dist}} {{comps}}
    - require:
      - file: remove-default-repos{{suf}}
    {% if root=='' %}
    - require_in:
      - pkg: ubuntu-pkgs
      - pkg: sys-pkgs
      - pkg: dev-pkgs
      - pkg: net-pkgs
      - pkg: salt-pkgs
    {% endif %}
main-src-repos{{suf}}:
  file.append:
    - name: {{root}}/etc/apt/sources.list
    - text: deb-src {{mirror}} {{dist}} {{comps}}
    - require:
      - file: remove-default-repos{{suf}}
    {% if root=='' %}
    - require_in:
      - pkg: ubuntu-pkgs
      - pkg: sys-pkgs
      - pkg: dev-pkgs
      - pkg: net-pkgs
      - pkg: salt-pkgs
    {% endif %}
{% endif %}
{% if grains['os'] == 'Ubuntu' %}
main-repos-updates{{suf}}:
  file.append:
    - name: {{root}}/etc/apt/sources.list
    - text: deb {{mirror}} {{dist}}-updates {{comps}}
    - require:
      - file: remove-default-repos{{suf}}
    {% if root=='' %}
    - require_in:
      - pkg: sys-pkgs
      - pkg: dev-pkgs
      - pkg: net-pkgs
      - pkg: salt-pkgs
    {% endif %}
{% endif %}
{% endmacro %}
{{ set_packages_repos()}}

{% if grains['os'] == 'Ubuntu' -%}
ubuntu-pkgs:
  pkg.installed:
    - names:
      - language-pack-en
      - language-pack-fr
      - python-software-properties
      - ubuntu-minimal
      - ubuntu-standard
      - apport
      - rsyslog
{% endif %}

sys-pkgs:
  pkg.installed:
    - names:
      - acpid
      - atop
      - bash-completion
      - bzip2
      - cron
      - cronolog
      - dialog
      - findutils
      - htop
      - links
      - locales
      - man-db
      - libopts25
      - manpages
      - manpages-fr
      - manpages-de
      - lsof
      - lvm2
      - lynx
      - mc
      - mlocate
      - ncdu
      - psmisc
      - pwgen
      - python
      - python-dev
      - sudo
      - screen
      - smartmontools
      - tmux
      - screen
      - tzdata
      - tree
      - unzip
      - vim
      - xfsprogs
      - zerofree
      - zip
      {% if grains['os_family'] == 'Debian' -%}
      - debconf-utils
      - dstat
      {% endif %}


{% if grains.get('makina.devhost', False) %}
devhost-pkgs:
  pkg.installed:
    - names:
      - localepurge
{% endif %}

dev-pkgs:
  pkg.installed:
    - names:
      - git
      - git-core
      {% if grains['os_family'] == 'Debian' -%}
      - build-essential
      - m4
      - libtool
      - pkg-config
      - autoconf
      - gettext
      - groff
      - automake
      - libsigc++-2.0-dev
      - tcl8.5
      {% endif %}

net-pkgs:
  pkg:
    - installed
    - names:
      - dnsutils
      - ethtool
      - ifenslave-2.6
      - iftop
      - iptraf
      - net-tools
      - nmap
      - ntp
      - openssh-server
      - rsync
      - sipcalc
      - tcpdump
      - telnet
      - traceroute
      - vlan
      - vnstat
      - wakeonlan
      - wget
      - whois

salt-pkgs:
  pkg.installed:
    - names:
      - python-apt
