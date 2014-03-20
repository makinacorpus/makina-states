{% import "makina-states/_macros/services.jinja" as services with context %}
{% set lxcSettings = services.lxcSettings %}

include:
  - makina-states.services.cloud.lxc.hooks

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
    - watch:
      - file: {{grains.id}}-download-{{name}}-{{tversion}}
    - watch_in:
      - mc_proxy: salt-cloud-lxc-images-download
      - mc_proxy: salt-cloud-lxc-default-template
{% endfor %}
