{% import "makina-states/_macros/services.jinja" as services with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{% set localsettings = services.localsettings %}

include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.services.virt.lxc-hooks
  - makina-states.services.cloud.salt_cloud-hooks
  - makina-states.services.cloud.lxc-hooks
{% for name, imgdata in lxcSettings.images.items() %}
{% set cwd = '/var/lib/lxc/{0}'.format(name) %}
{% set arc = '{0}/{1}'.format(name, imgdata['lxc_tarball_name']) %}
{% set tversion  = imgdata['lxc_tarball_ver'] %}
{{grains.id}}-download-{{name}}-{{tversion}}:
  file.directory:
    - name: {{cwd}}
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
  archive.extracted:
    - name: {{cwd}}
    - source: {{imgdata.lxc_tarball}}
    - source_hash: md5={{imgdata.lxc_tarball_md5}}
    - archive_format: tar
    - if_missing: {{cwd}}/rootfs/etc/salt
    - tar_options: -xJf
    - require:
      - file: {{grains.id}}-download-{{name}}-{{tversion}}
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-restore-specialfiles-{{name}}:
  cmd.run:
    - name: cp -a /dev/log {{cwd}}/rootfs/dev/log
    - unless: test -e {{cwd}}/rootfs/dev/log
    - cwd: {{cwd}}
    - user: root
    - require:
      - archive: {{grains.id}}-download-{{name}}-{{tversion}}
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-restore-acls-{{name}}:
  cmd.run:
    - name: setfacl --restore=acls.txt && touch acls_done
    - cwd: {{cwd}}
    - unless: test -e {{cwd}}/acls_done
    - user: root
    - require:
      - cmd: {{grains.id}}-restore-specialfiles-{{name}}
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-{{name}}-stop-default-lxc-container:
  lxc.stopped:
    - name: {{name}}
    - require:
      - cmd: {{grains.id}}-restore-specialfiles-{{name}}
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-{{name}}-lxc-snap:
  cmd.run:
    - name: chroot /var/lib/lxc/{{name}}/rootfs/ /sbin/lxc-snap.sh
    - onlyif: test -e /var/lib/lxc/{{name}}/rootfs/etc/salt/pki/minion/minion.pub
    - require:
      - lxc: {{grains.id}}-{{name}}-stop-default-lxc-container
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-{{name}}-lxc-removeminion:
  file.absent:
    - name: {{cloudSettings.prefix}}/pki/master/minions/{{name}}
    - require:
      - cmd: {{grains.id}}-{{name}}-lxc-snap
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template
{% endfor %}
