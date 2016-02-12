{% set data = salt['mc_ntp.settings']() %}
include:
  - makina-states.services.base.ntp.hooks
{% if not salt['mc_nodetypes.is_docker']() %}
ntpd-uninstall-svc:
  service.dead:
    - enable: false
    - watch_in:
      - mc_proxy: ntp-post-restart-hook
    - watch:
      - mc_proxy: ntp-pre-restart-hook
    - name: ntp

ntpd-killall-svc:
  cmd.run:
    - name: |
            is_lxc() {
                echo  "$(cat -e /proc/1/environ |grep container=lxc|wc -l|sed -e "s/ //g")"
            }
            filter_host_pids() {
                if [ "x$(is_lxc)" != "x0" ];then
                    echo "${@}"
                else
                    for pid in ${@};do
                        if [ "x$(grep -q lxc /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ];then
                             echo ${pid}
                         fi
                     done
                fi
            }
            for i in $(filter_host_pids $(ps aux|grep /usr/sbin/ntpd|grep -v grep|awk '{print $2}'));do kill -9 $i;done
            /bin/true
            echo changed=false
    - stateful: true
    - watch_in:
      - mc_proxy: ntp-post-restart-hook
    - watch:
      - mc_proxy: ntp-pre-restart-hook
{%- endif %}
