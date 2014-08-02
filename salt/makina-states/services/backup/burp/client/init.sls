{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('services', 'backup.burp.client') }}
include:
  - makina-states.services.backup.burp.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services.backup.burp.server.prerequisites
{% endif %}

{# install on an unmanaged box
git clone https://github.com/grke/burp.git 
cd burp 
git checkout remotes/origin/1.3.48
apt-get install  -y build-essential  librsync-dev libz-dev libssl-dev uthash-dev libacl1-dev libncurses5-dev 
./configure  && make && make install
#}
