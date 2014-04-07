include:
  - makina-states.localsettings.npm.hooks
{%  if grains['os'] in ['Debian'] %}
npm-pkgs:
  file.symlink:
    - target: {{locs.bin_dir}}/nodejs
    - name: {{locs.bin_dir}}/node
    - watch:
      - mc_proxy: nodejs-pre-system-install
  cmd.run:
    - unless: which npm
    - name: >
            . /etc/profile &&
            curl -s https://npmjs.org/install.sh -o /tmp/npminstall &&
            chmod +x /tmp/npminstall &&
            /tmp/npminstall && rm -f /tmp/npminstall;
    - watch_in:
      - mc_proxy: nodejs-post-system-install
    - watch:
      - file: npm-pkgs
      - mc_proxy: nodejs-pre-system-install
      - pkg: nodejs-pkgs
{% endif %}
