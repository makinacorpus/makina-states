#!/usr/bin/env bash
PS="ps"
TIMEOUT=$((60*60*24*2))

is_container() {
    cat -e /proc/1/environ 2>/dev/null|grep -q container=
    echo "${?}"
}

filter_host_pids() {
    pids=""
    if [ "x$(is_container)" = "x0" ];then
        pids="${pids} $(echo "${@}")"
    else
        for pid in ${@};do
            if [ "x$(grep -q /lxc/ /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ];then
                pids="${pids} $(echo "${pid}")"
            fi
         done
    fi
    echo "${pids}" | sed -e "s/\(^ \+\)\|\( \+$\)//g"
}

burp_client() {
    filter_host_pids $(${PS} aux|grep burp|grep -- "-a t"|grep -v grep|awk '{print $2}')|wc -w|sed -e "s/ //g"
}
ps_etime() {
    ${PS} -eo pid,comm,etime,args | perl -ane '@t=reverse(split(/[:-]/, $F[2])); $s=$t[0]+$t[1]*60+$t[2]*3600+$t[3]*86400;$cmd=join(" ", @F[3..$#F]);print "$F[0]\t$s\t$F[1]\t$F[2]\t$cmd\n"'
}
kill_old_syncs() {
    # kill all stale synchronnise code jobs
    while read psline;
    do
        pid="$(filter_host_pids $(echo $psline|awk '{print $1}'))"
        boottime=$(cat /proc/stat  | awk '/btime/ { print $2 }')
        now=$(date +%s)

        if [ "x${pid}" != "x" ];then
            starttime_from_boot=$(awk '{print int($22 / 100)}' /proc/$pid/stat)
            starttime=$((boottime + starttime_from_boot))

            seconds=$((now - starttime))
            # 8 minutes
            if [ "${seconds}" -gt "${TIMEOUT}" ];then
                echo "Something was wrong with last backup, killing old sync processes: $pid"
                echo "${psline}"
                kill -9 "${pid}"
                todo="y"
            fi
        fi
    done < <( ps_etime|sort -n -k2|grep burp|grep -- "-a t"|grep -v grep )
    lines="$(filter_host_pids $(ps aux|grep burp|grep -- '-a t'|awk '{print $2}')|wc -l|sed 's/ +//g')"
    if [ "x${lines}" = "x0" ];then
        if [ -f /var/run/burp.client.pid ];then
            todo="y"
            rm -f /var/run/burp.client.pid
        fi
    fi
}

todo=""
kill_old_syncs
# trigger a backup try if we were killed
if [ "x${todo}" != "x" ];then
    burp -a t
fi
# vim:set et sts=4 ts=4 tw=0:
