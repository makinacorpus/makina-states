{# WARNING THIS STATE FILE IS GENERATED #}
{% set imgSettings = salt['mc_utils.json_load'](pillar.simgSettings) %}
{% set cloudSettings = salt['mc_utils.json_load'](pillar.scloudSettings) %}
{% set sprefix = cloudSettings.prefix %}
include:
  - makina-states.cloud.generic.hooks.generate
{% for name, imgdata in imgSettings.items() %}
{% set cwd = '/var/lib/lxc/{0}'.format(name) %}
{% set arc = '{0}/{1}'.format(name, imgdata['lxc_tarball_name']) %}
{% set tversion  = imgdata['lxc_tarball_ver'] %}
download-{{name}}-{{tversion}}:
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
    - watch:
      - file: download-{{name}}-{{tversion}}
restore-specialfiles-{{name}}:
  cmd.run:
    - name: cp -a /dev/log {{cwd}}/rootfs/dev/log
    - unless: test -e {{cwd}}/rootfs/dev/log
    - cwd: {{cwd}}
    - user: root
    - watch:
      - archive: download-{{name}}-{{tversion}}
restore-acls-{{name}}:
  cmd.run:
    - name: setfacl --restore=acls.txt && touch acls_done
    - cwd: {{cwd}}
    - unless: test -e {{cwd}}/acls_done
    - user: root
    - watch:
      - cmd: restore-specialfiles-{{name}}
{{name}}-stop-default-lxc-container:
  lxc.stopped:
    - name: {{name}}
    - watch:
      - cmd: restore-specialfiles-{{name}}
{{name}}-lxc-snap:
  cmd.run:
    - name: chroot /var/lib/lxc/{{name}}/rootfs /sbin/lxc-snap.sh
    - onlyif: test -e /var/lib/lxc/{{name}}/rootfs/etc/salt/pki/minion/minion.pub
    - watch:
      - lxc: {{name}}-stop-default-lxc-container
{{name}}-lxc-removeminion:
  file.absent:
    - name: {{sprefix}}/pki/master/minions/{{name}}
    - watch:
      - cmd: {{name}}-lxc-snap
{% endfor %}
maybe-only-one-gen-lxc-images:
  mc_proxy.hook : []
