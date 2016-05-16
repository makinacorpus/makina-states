include:
 - makina-states.localsettings.rvm.hooks
{%- set rvms = salt['mc_rvm.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- import "makina-states/localsettings/rvm/macros.jinja" as rvmmac %}

{%- for ruby in rvms.rubies %}
{{    rvmmac.install_ruby(ruby) }}
{%- endfor %}

active-rvm-bundler-hook:
  cmd.run:
    - name: {{locs.resetperms}} --no-acls --dmode 0700 --fmode 0700 --paths "{{locs.rvm_path}}/hooks/after_cd_bundler"
    - require:
      - mc_proxy: rvm-setup-act-pre
    - require_in:
      - mc_proxy: rvm-setup-act-post
