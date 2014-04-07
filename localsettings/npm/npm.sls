{% set localsettings = salt['mc_localsettings.settings']()%}
{% set locs = localsettings.locations %}
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
{% for npmPackage in npmPackages -%}
{{ npmInstall(npmPackage) }}
{%- endfor %}
{% for ver, package in npmAppPackages.items() %}
{{npmInstall(package, version=ver}}
{% endfor %}
