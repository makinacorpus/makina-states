NP_VER="1.1.1"
rm -f nagios-snmp-plugins.${NP_VER}.tgz
wget http://nagios.manubulon.com/nagios-snmp-plugins.${NP_VER}.tgz
tar xzf nagios-snmp-plugins.${NP_VER}.tgz
sed -i -e 's:\(/usr/local/nagios/libexec";\):\1use lib "/usr/lib/nagios/plugins/";:g'  nagios_plugins/*pl
sed -i -e 's/Net::SNMP->VERSION < 4/Net::SNMP->VERSION lt 4/g' nagios_plugins/*pl
cp -f nagios_plugins/*pl .
rm -rf nagios_plugins nagios*plugins*gz*
