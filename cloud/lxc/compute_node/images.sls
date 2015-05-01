{# WARNING THIS STATE FILE IS GENERATED #}
{% set imgSettings = salt['mc_cloud_images.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set sprefix = cloudSettings.prefix %}
{% for name, imgdata in imgSettings['lxc']['images'].items() %}
{% if imgdata.get('lxc_tarball_ver', '') %}
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
  cmd.run:
    - onlyif: test ! -e "{{cwd}}/rootfs/etc/salt"
    - use_vt: true
    - name: |
            set -x;
            dest="{{cwd}}/../$(basename "{{imgdata.lxc_tarball}}")"
            if [ -e "${dest}" ];then
              if [ "x$(md5sum "${dest}"|awk '{print $1}')" != "x{{imgdata.lxc_tarball_md5}}" ];then
                rm -f "${dest}"
              fi
            fi
            if [ ! -e "${dest}" ];then
              cd "{{cwd}}/.."
              wget --no-check-certificate "{{imgdata.lxc_tarball}}";
            fi
            cd "{{cwd}}"
            tar xJf "${dest}";
    - watch:
      - file: download-{{name}}-{{tversion}}
  archive.extracted:
    - name: {{cwd}}
    - source:
    - source_hash: md5=
    - archive_format: tar
    - if_missing:
    - tar_options: xJ

restore-specialfiles-{{name}}:
  cmd.run:
    - name: cp -a /dev/log {{cwd}}/rootfs/dev/log
    - unless: test -e {{cwd}}/rootfs/dev/log
    - cwd: {{cwd}}
    - user: root
    - watch:
      - cmd: download-{{name}}-{{tversion}}
# more harm than good, let highstate restore them
# restore-acls-{{name}}:
#   cmd.run:
#     - name: setfacl --restore=acls.txt;touch acls_done
#     - cwd: {{cwd}}
#     - unless: test -e {{cwd}}/acls_done
#     - user: root
#     - watch:
#       - cmd: restore-specialfiles-{{name}}
{{name}}-stop-default-lxc-container:
  lxc.stopped:
    - name: {{name}}
    - watch:
      - cmd: restore-specialfiles-{{name}}
{{name}}-makinastates-snapshot:
  cmd.run:
    - name: chroot /var/lib/lxc/{{name}}/rootfs /sbin/makinastates-snapshot.sh
    - onlyif: test -e /var/lib/lxc/{{name}}/rootfs/etc/salt/pki/minion/minion.pub
    - watch:
      - lxc: {{name}}-stop-default-lxc-container
{{name}}-lxc-removeminion:
  file.absent:
    - name: {{sprefix}}/pki/master/minions/{{name}}
    - watch:
      - cmd: {{name}}-makinastates-snapshot
{% endif %}
{% endfor %}
maybe-only-one-gen-lxc-images:
  mc_proxy.hook : []
