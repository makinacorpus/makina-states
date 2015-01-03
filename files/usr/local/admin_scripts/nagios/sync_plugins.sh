#!/usr/bin/env bash
cd $(dirname $0)
#manibulons
NP_VER="1.1.1"
rm -f nagios-snmp-plugins.${NP_VER}.tgz
wget http://nagios.manubulon.com/nagios-snmp-plugins.${NP_VER}.tgz
tar xzf nagios-snmp-plugins.${NP_VER}.tgz
sed -i -e 's:\(/usr/local/nagios/libexec";\):\1use lib "/usr/lib/nagios/plugins/";:g'  nagios_plugins/*pl
sed -i -e 's/Net::SNMP->VERSION < 4/Net::SNMP->VERSION lt 4/g' nagios_plugins/*pl
cp -f nagios_plugins/*pl .
rm -rf nagios_plugins nagios*plugins*gz*
#centreon plugins
wget "http://download.centreon.com/index.php?id=4320" -O centreonp.tgz
tar xzf centreonp.tgz
rsync -azv --delete centreon-*/plugins/ centreon_plugins/
find centreon_plugins/src/ -type f |xargs sed -i -re "s:@NAGIOS_PLUGINS@:/usr/local/admin_scripts/nagios/centreon_plugins/src:g"
find centreon_plugins/src/ -type f |xargs sed -i -re "s:@CENTPLUGINS_TMP@:/tmp:g"
chmod +x  centreon_plugins/src/chec* centreon_plugins/src/*resul*
rm -rf centreon-* centreo*tgz
for i in $(find -type f);do
    if [ "x$(grep -q /local/lib/nagios/plugins $i;echo $?)" != "x0" ];then
        sed -i -re "s|use lib '/usr/lib/nagios/plugins/?';|use lib '/usr/lib/nagios/plugins';use lib '/usr/local/lib/nagios/plugins';|g" $i
        sed -i -re "s|use lib \"/usr/lib/nagios/plugins/?\";|use lib '/usr/lib/nagios/plugins';use lib '/usr/local/lib/nagios/plugins';|g" $i
    fi
done
rm -f check_mem.pl check_mem.php

wget "https://raw.githubusercontent.com/justintime/nagios-plugins/master/check_mem/check_mem.pl"
wget "https://raw.githubusercontent.com/justintime/nagios-plugins/master/check_mem/check_mem.php"

wget "http://labs.consol.de/download/shinken-nagios-plugins/check_mysql_health-2.1.8.2.tar.gz"
tar xzvf check_mysql_health-*z
cd check_mysql_health-2* && ./configure --with-statefiles-dir=/tmp --prefix=$PWD && make && make install && cp -f libexec/check* ..
rm -f check_mysql_health-*z check_mysql_health-2*

cp /usr/lib/nagios/plugins/check_http .

wget "http://bucardo.org/downloads/check_postgres-2.21.0.tar.gz"
tar xzvf check_postgres-*z
cp -f check_postgres-2.21.0/check_postgres.pl ./
rm -f check_postgres-*z check_postgres-2*

rm -f check_mongodb.py
wget "https://github.com/mzupan/nagios-plugin-mongodb/raw/master/check_mongodb.py"
chmod +x check_mongodb.py

rm -f check_elasticsearch
wget "https://github.com/anchor/nagios-plugin-elasticsearch/raw/master/check_elasticsearch"
chmod +x check_elasticsearch

wget https://raw.github.com/glensc/nagios-plugin-check_raid/master/check_raid.pl -O check_raid.pl
chmod +x check_raid.pl 


echo "dont forget changes to snmp traffic (, -> . for perfdata)"
echo "sync http://exchange.nagios.org/directory/Plugins/Operating-Systems/Linux/check_linux_stats/details"

wget "https://fidanov.net/c0d3/nagios-plugins/mio/check_mio" -O check_mio
chmod +x "check_mio"

wget https://raw.githubusercontent.com/egeland/nagios-rbl-check/master/check_rbl.py -O check_rbl.py
chmod +x check_rbl.py

wget "https://raw.githubusercontent.com/willixix/WL-NagiosPlugins/master/check_redis.pl" -O check_redis.pl
chmod +x check_redis.pl
