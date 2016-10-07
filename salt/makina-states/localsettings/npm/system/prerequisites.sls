include:
  - makina-states.localsettings.npm.hooks
  - makina-states.localsettings.nodejs.system
{# retrocompat states, as now only the nodejs state suffice #}
npm-pkgs:
  file.exists:
    - names:
        - /usr/bin/nodejs
        - /usr/bin/node
        - /usr/bin/npm
    - watch:
      - mc_proxy: nodejs-pre-system-install
  cmd.run:
    - name: /bin/false
    - onlyif: test ! -e /usr/bin/npm
    {# disabled
    - unless: which npm
            . /etc/profile &&
            curl -s https://npmjs.org/install.sh -o /tmp/npminstall &&
            chmod +x /tmp/npminstall &&
            /tmp/npminstall && rm -f /tmp/npminstall;
    #}
    - watch_in:
      - mc_proxy: nodejs-post-system-install
    - watch:
      - file: npm-pkgs
      - mc_proxy: nodejs-pre-system-install
