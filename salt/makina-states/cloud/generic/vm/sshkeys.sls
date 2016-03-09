{% set cloudSettings = salt['mc_cloud.settings']() %} 
include:
    - makina-states.services.base.ssh.rootkey
{% for k in ['rsa', 'dsa'] %}
check{{k}}noref-key:
  cmd.run:
    - name: |
            if [ ! -e /root/.ssh/salt.sav.id_{{k}}.salt.sav ];then
              mkdir -pv /root/.ssh/salt.sav.id_{{k}}
            fi
            if [ "x$(egrep -q "lxc.*ref" /root/.ssh/id_{{k}}*;echo $?)" = "x0" ];then
              mv -f /root/.ssh/id_{{k}}* /root/.ssh/salt.sav.id_{{k}}
            fi
    - user: root
    - unless: >
              test ! -e "/root/.ssh/id_{{k}}" &&
              test "x$(egrep -q "lxc.*ref" /root/.ssh/id_{{k}}*;echo $?)" != "x0"
    - onlyif: test "x$(egrep -q "lxc.*ref" /root/.ssh/id_{{k}}*;echo $?)" = "x0"
    - watch_in:
      - cmd: root-ssh-keys-init

ins{{k}}key:
  ssh_auth.present:
    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-{{k}}.pub
    - user: root
{% endfor %}
