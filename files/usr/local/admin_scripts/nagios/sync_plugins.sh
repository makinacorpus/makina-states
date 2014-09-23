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
