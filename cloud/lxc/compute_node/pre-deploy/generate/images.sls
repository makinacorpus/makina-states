include:
  - makina-states.cloud.generic.hooks.compute_node
{% set csettings = salt['mc_cloud.settings']() %}
{% set imgSettings = salt['mc_cloud_images.settings']() %}
{% set settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in settings['targets'].iteritems() %}
{% if data.has.lxc %}
{% set cptslsname = '{1}/{0}/lxc-images-templates'.format(target.replace('.', ''),
                                                 csettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
{{target}}-gen-lxc-images-templates:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - watch:
      - mc_proxy.hook: cloud-generic-compute_node-pre-images-deploy
    - watch_in:
      - mc_proxy.hook: cloud-{{target}}-generic-compute_node-pre-images-deploy
    - contents: |
            {% for name, imgdata in imgSettings.lxc.images.items() %}
            {% set cwd = '/var/lib/lxc/{0}'.format(name) %}
            {% set arc = '{0}/{1}'.format(name, imgdata['lxc_tarball_name']) %}
            {% set tversion  = imgdata['lxc_tarball_ver'] %}
            {{target}}-download-{{name}}-{{tversion}}:
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
                  - file: {{target}}-download-{{name}}-{{tversion}}
                - watch_in:
                  - mc_proxy: salt-cloud-lxc-images-download
            {{target}}-restore-specialfiles-{{name}}:
              cmd.run:
                - name: cp -a /dev/log {{cwd}}/rootfs/dev/log
                - unless: test -e {{cwd}}/rootfs/dev/log
                - cwd: {{cwd}}
                - user: root
                - watch:
                  - archive: {{target}}-download-{{name}}-{{tversion}}
            {{target}}-restore-acls-{{name}}:
              cmd.run:
                - name: setfacl --restore=acls.txt && touch acls_done
                - cwd: {{cwd}}
                - unless: test -e {{cwd}}/acls_done
                - user: root
                - watch:
                  - cmd: {{target}}-restore-specialfiles-{{name}}
            {{target}}-{{name}}-stop-default-lxc-container:
              lxc.stopped:
                - name: {{name}}
                - watch:
                  - cmd: {{target}}-restore-specialfiles-{{name}}
            {{target}}-{{name}}-lxc-snap:
              cmd.run:
                - name: chroot /var/lib/lxc/{{name}}/rootfs/sbin/lxc-snap.sh
                - onlyif: test -e /var/lib/lxc/{{name}}/rootfs/etc/salt/pki/minion/minion.pub
                - watch:
                  - lxc: {{target}}-{{name}}-stop-default-lxc-container
            {{target}}-{{name}}-lxc-removeminion:
              file.absent:
                - name: {{csettings.prefix}}/pki/master/minions/{{name}}
                - watch:
                  - cmd: {{target}}-{{name}}-lxc-snap
            {% endfor %}
{% endif %}
{% endfor %}
maybe-only-one-gen-lxc-images:
  mc_proxy.hook : []

