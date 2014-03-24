{% set csettings = salt['mc_cloud.settings']() %}
{% set imgSettings = salt['mc_cloud_images.settings']() %}
{% set settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in settings['targets'].iteritems() %}
{% if data.has.lxc %}
{% set cptslsname = '{1}/{0}/lxc-images-templates'.format(target.replace('.', ''),
                                                 csettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
# get an haproxy proxying all request on 80+43 + alternate ports for ssh traffic
{% set sdata = data|yaml %}
{% set sdata = sdata.replace('\n', ' ') %}
{{target}}-gen-lxc-images-templates:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
            include:
              - makina-states.cloud.lxc.hooks
            {% for name, imgdata in imgSettings.lxc.images.items() %}
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
                - watch:
                  - file: {{grains.id}}-download-{{name}}-{{tversion}}
                - watch_in:
                  - mc_proxy: salt-cloud-lxc-images-download
                  - mc_proxy: salt-cloud-lxc-default-template
            {{grains.id}}-restore-specialfiles-{{name}}:
              cmd.run:
                - name: cp -a /dev/log {{cwd}}/rootfs/dev/log
                - unless: test -e {{cwd}}/rootfs/dev/log
                - cwd: {{cwd}}
                - user: root
                - watch:
                  - archive: {{grains.id}}-download-{{name}}-{{tversion}}
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
                - name: {{csettings.prefix}}/pki/master/minions/{{name}}
                - watch:
                  - cmd: {{grains.id}}-{{name}}-lxc-snap
                - watch_in:
                  - mc_proxy: salt-cloud-lxc-default-template
            {% endfor %}
{% endif %}
{% endfor %}
maybe-only-one-gen-lxc-images:
  mc_proxy.hook : []

