{% set locs = salt['mc_locations.settings']() %}
{% set nodejs = salt['mc_nodejs.settings']() %}
{% macro npmInstall(npmPackage, npmVersion="system") %}
npm-packages-{{npmPackage}}:
  cmd.run:
    - watch
      - mc_proxy: npm-installation
    {% if npmVersion == "system" %}
    - name: npm install -g {{npmPackage}}
    {% else %}
    - name: |
            export PATH={{ locs['apps_dir'] }}/nodejs/{{ npmVersion }}/bin:$PATH;
            if [ ! -e {{ locs['apps_dir'] }}/nodejs/{{ npmVersion }}/bin/npm ];
            then exit 1;
            else npm install -g {{npmPackage}};
            fi
    {% endif %}
{% endmacro %}
{% for package, vers in nodejs.systemNpmPackages %}
{% for ver in vers %}
{{npmInstall(package, versio=ver)}}
{% endfor %}
{% endfor %}
