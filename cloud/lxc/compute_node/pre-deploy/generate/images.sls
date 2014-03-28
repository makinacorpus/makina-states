include:
  - makina-states.cloud.generic.hooks.generate
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set imgSettings = salt['mc_cloud_images.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{% if 'lxc' in data.virt_types %}
{% set cptslsname = '{1}/{0}/lxc/compute_node_images-templates'.format(target.replace('.', ''),
                                                 cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{% set rcptslsname = '{1}/{0}/lxc/run-compute_node_images-templates'.format(target.replace('.', ''),
                                                 cloudSettings.compute_node_sls_dir) %}
{% set rcptsls = '{1}/{0}.sls'.format(rcptslsname, cloudSettings.root) %}
{{target}}-install-lxc-images-templates-gen-inst:
  file.managed:
    - name: {{rcptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: {{localsettings.group}}
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - contents: |
                {%raw%}{# WARNING THIS STATE FILE IS GENERATED #}{%endraw%}
                include:
                  - makina-states.cloud.generic.hooks.compute_node
                {{target}}-lxc-install-base-imgs:
                  salt.state:
                    - tgt: [{{target}}]
                    - expr_form: list
                    - sls: {{cptslsname.replace('/', '.')}}
                    - concurrent: True
                    - watch:
                      - mc_proxy: cloud-generic-compute_node-pre-images-deploy
                    - watch_in:
                      - mc_proxy: cloud-generic-compute_node-post-images-deploy
{{target}}-gen-lxc-images-templates:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: {{localsettings.group}}
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - contents: |
                {%raw%}{# WARNING THIS STATE FILE IS GENERATED #}{%endraw%}
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
                    - name: {{cloudSettings.prefix}}/pki/master/minions/{{name}}
                    - watch:
                      - cmd: {{target}}-{{name}}-lxc-snap
                {% endfor %}
{% endif %}
{% endfor %}
maybe-only-one-gen-lxc-images:
  mc_proxy.hook : []

