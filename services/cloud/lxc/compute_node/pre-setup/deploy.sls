{% set cloudSettings = salt['mc_cloud_controller.settings']() %}
{% set imgSettings = salt['mc_cloud_images.settings']() %}

include:
  - makina-states.services.cloud.lxc.hooks
{% for name, imgdata in imgSettings.lxc.images.items() %}
{% set cwd = '/var/lib/lxc/{0}'.format(name) %}
{% set arc = '{0}/{1}'.format(name, imgdata['lxc_tarball_name']) %}
{% set tversion  = imgdata['lxc_tarball_ver'] %}

{{grains.id}}-restore-specialfiles-{{name}}:
  cmd.run:
    - name: cp -a /dev/log {{cwd}}/rootfs/dev/log
    - unless: test -e {{cwd}}/rootfs/dev/log
    - cwd: {{cwd}}
    - user: root
    - watch:
      - mc_proxy: salt-cloud-lxc-images-download
    - watch_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-restore-acls-{{name}}:
  cmd.run:
    - name: setfacl --restore=acls.txt && touch acls_done
    - cwd: {{cwd}}
    - unless: test -e {{cwd}}/acls_done
    - user: root
    - watch:
      - cmd: {{grains.id}}-restore-specialfiles-{{name}}
    - watch_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-{{name}}-stop-default-lxc-container:
  lxc.stopped:
    - name: {{name}}
    - watch:
      - cmd: {{grains.id}}-restore-specialfiles-{{name}}
    - watch_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-{{name}}-lxc-snap:
  cmd.run:
    - name: chroot /var/lib/lxc/{{name}}/rootfs/sbin/lxc-snap.sh
    - onlyif: test -e /var/lib/lxc/{{name}}/rootfs/etc/salt/pki/minion/minion.pub
    - watch:
      - lxc: {{grains.id}}-{{name}}-stop-default-lxc-container
    - watch_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-{{name}}-lxc-removeminion:
  file.absent:
    - name: {{cloudSettings.prefix}}/pki/master/minions/{{name}}
    - watch:
      - cmd: {{grains.id}}-{{name}}-lxc-snap
    - watch_in:
      - mc_proxy: salt-cloud-lxc-default-template

{% endfor %}
