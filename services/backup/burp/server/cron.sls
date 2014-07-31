{% set data = salt['mc_burp.settings']() %}
{% if salt['mc_controllers.mastersalt_mode']() %}
burp-cron-cmd:
  file.managed:
    - name: /usr/bin/burp-cron.sh
    - makedirs: true
    - mode: 755
    - contents: |
                #!/usr/bin/env bash
                . /etc/profile
                LOG="/var/log/burpcron.log"
                lock="${0}.lock"
                if [ -e "${lock}" ];then
                  echo "Locked ${0}";exit 1
                fi
                touch "${lock}"
                mastersalt-call --out-file="${LOG}" --retcode-passthrough -lall \
                   state.sls makina-states.services.backup.burp.server 1>/dev/null 2>/dev/null
                ret="${?}"
                rm -f "${lock}"
                if [ "x${ret}" != "x0" ];then
                  cat "${LOG}"
                fi
                exit "${ret}"
    - user: root
    - use_vt: true

{% if data.cron_activated %}
burp-cron:
  file.managed:
    - name: "/etc/cron.d/burpsynccron"
    - contents: |
                #!/usr/bin/env bash
                MAILTO="{{data.admins}}"
                {{data.cron_periodicity}} root su -c "/usr/bin/burp-cron.sh"
    - user: root
    - makedirs: true
    - use_vt: true
    - require:
      - file: burp-cron-cmd
{% else %}
burp-cron:
  file.absent:
    - name: "/etc/cron.d/burpsynccron"
{% endif %}
{% endif %}
