#!/usr/bin/perl -w
# check_laborange_stats
# Version : 1.0
# Author  : regis.leroy at makina-corpus.com
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
#
# help : ./check_laborange_stats.pl -h
#
# issues & updates: http://github.com/regilero/check_inginx_status
use strict;
use Getopt::Long;
use LWP::UserAgent;
use Time::HiRes qw(gettimeofday tv_interval);
use Digest::MD5 qw(md5 md5_hex);


# Nagios specific
use lib "/usr/local/nagios/libexec";
use utils qw($TIMEOUT);

# Globals
my $Version='0.9';
my $Name=$0;

my $o_host =          undef;  # hostname 
my $o_help=           undef;  # want some help ?
my $o_port=           undef;  # port
my $o_url =           undef;  # url to use, if not the default
my $o_user=           undef;  # user for auth
my $o_pass=           '';     # password for auth
my $o_realm=          '';     # password for auth
my $o_version=        undef;  # print version
my $o_warn_a_level=   -1;     # Number of active connections that will cause a warning
my $o_crit_a_level=   -1;     # Number of active connections that will cause an error
my $o_timeout=        15;     # Default 15s Timeout
my $o_warn_thresold=  undef;  # warning thresolds entry
my $o_crit_thresold=  undef;  # critical thresolds entry
my $o_debug=          undef;  # debug mode
my $o_servername=     undef;  # ServerName (host header in http request)
my $o_https=          undef;  # SSL (HTTPS) mode

my $TempPath = '/tmp/';     # temp path
my $MaxTimeDif = 60*30;   # Maximum uptime difference (seconds), default 30 minutes

my $check='LABSTATS';

# functions
sub show_versioninfo { print "$Name version : $Version\n"; }

sub print_usage {
  print "Usage: $Name -H <host ip> [-p <port>] [-s servername] [-t <timeout>] [-w <WARN_THRESOLD> -c <CRIT_THRESOLD>] [-V] [-d] [-u <url>] [-U user -P pass -r realm]\n";
}
sub nagios_exit {
    my ( $nickname, $status, $message, $perfdata , $silent) = @_;
    my %STATUSCODE = (
      'OK' => 0
      , 'WARNING' => 1
      , 'CRITICAL' => 2
      , 'UNKNOWN' => 3
      , 'PENDING' => 4
    );
    if(!defined($silent)) {
        my $output = undef;
        $output .= sprintf('%1$s %2$s - %3$s', $nickname, $status, $message);
        if ($perfdata) {
            $output .= sprintf('|%1$s', $perfdata);
        }
        $output .= chr(10);
        print $output;
    }
    exit $STATUSCODE{$status};
}

# Get the alarm signal
$SIG{'ALRM'} = sub {
  nagios_exit($check,"CRITICAL","ERROR: Alarm signal (Nagios timeout)");
};

sub help {
  print "Laborange internal stats Monitor for Nagios version ",$Version,"\n";
  print "GPL licence, (c)2012 Leroy Regis\n\n";
  print_usage();
  print <<EOT;
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-p, --port=PORT
   Http port
-u, --url=URL
   Specific URL to use, instead of the default "http://<hostname or IP>/nginx_status"
-s, --servername=SERVERNAME
   ServerName, (host header of HTTP request) use it if you specified an IP in -H to match the good Virtualhost in your target
-S, --ssl
   Wether we should use HTTPS instead of HTTP
-U, --user=user
   Username for basic auth
-P, --pass=PASS
   Password for basic auth
-r, --realm=REALM
   Realm for basic auth
-d, --debug
   Debug mode (show http request response)
-t, --timeout=INTEGER
   timeout in seconds (Default: $o_timeout)
-w, --warn=ACTIVE_CONN
   number of active connections that will cause a WARNING
   -1 for no warning
-c, --critical=ACTIVE_CONN
   number of active connections that will cause a CRITICAL
   -1 for no CRITICAL
-V, --version
   prints version number

EOT
}

sub check_options {
    Getopt::Long::Configure ("bundling");
    GetOptions(
      'h'     => \$o_help,         'help'          => \$o_help,
      'd'     => \$o_debug,        'debug'         => \$o_debug,
      'H:s'   => \$o_host,         'hostname:s'    => \$o_host,
      's:s'   => \$o_servername,   'servername:s'  => \$o_servername,
      'S:s'   => \$o_https,        'ssl:s'         => \$o_https,
      'u:s'   => \$o_url,          'url:s'         => \$o_url,
      'U:s'   => \$o_user,         'user:s'        => \$o_user,
      'P:s'   => \$o_pass,         'pass:s'        => \$o_pass,
      'r:s'   => \$o_realm,        'realm:s'       => \$o_realm,
      'p:i'   => \$o_port,         'port:i'        => \$o_port,
      'V'     => \$o_version,      'version'       => \$o_version,
      'w:s'   => \$o_warn_thresold,'warn:s'        => \$o_warn_thresold,
      'c:s'   => \$o_crit_thresold,'critical:s'    => \$o_crit_thresold,
      't:i'   => \$o_timeout,      'timeout:i'     => \$o_timeout,
    );

    if (defined ($o_help)) { 
        help();
        nagios_exit($check,"UNKNOWN","leaving","",1);
    }
    if (defined($o_version)) { 
        show_versioninfo();
        nagios_exit($check,"UNKNOWN","leaving","",1);
    };
    
    if (defined($o_warn_thresold)) {
        $o_warn_a_level = $o_warn_thresold;
    }
    if (defined($o_crit_thresold)) {
        $o_crit_a_level = $o_crit_thresold;
    }
    if (defined($o_debug)) {
        print("\nDebug thresolds: \nWarning: ($o_warn_thresold) => Active: $o_warn_a_level \n");
        print("\nCritical ($o_crit_thresold) => : Active: $o_crit_a_level \n");
    }
    if ((defined($o_warn_a_level) && defined($o_crit_a_level)) &&
         (($o_warn_a_level != -1) && ($o_crit_a_level != -1) && ($o_warn_a_level >= $o_crit_a_level)) ) { 
        nagios_exit($check,"UNKNOWN","Check warning and critical values for Active Process, warning level must be < crit level!");
    }
    # Check compulsory attributes
    if (!defined($o_host)) { 
        print_usage();
        nagios_exit($check,"UNKNOWN","-H host argument required");
    }
}

########## MAIN ##########

check_options();

my $override_ip = $o_host;
my $ua = LWP::UserAgent->new( 
  protocols_allowed => ['http', 'https'], 
  timeout => $o_timeout
);
# we need to enforce the HTTP request is made on the Nagios Host IP and
# not on the DNS related IP for that domain
@LWP::Protocol::http::EXTRA_SOCK_OPTS = ( PeerAddr => $override_ip );
# this prevent used only once warning in -w mode
my $ua_settings = @LWP::Protocol::http::EXTRA_SOCK_OPTS;

my $timing0 = [gettimeofday];
my $response = undef;
my $url = undef;

if (!defined($o_url)) {
    $o_url='/monitor-status.php?track';
} else {
    # ensure we have a '/' as first char
    $o_url = '/'.$o_url unless $o_url =~ m(^/)
}
my $proto='http://';
if(defined($o_https)) {
    $proto='https://';
    if (defined($o_port) && $o_port!=443) {
        if (defined ($o_debug)) {
            print "\nDEBUG: Notice: port is defined at $o_port and not 443, check you really want that in SSL mode! \n";
        }
    }
}
if (defined($o_servername)) {
    if (!defined($o_port)) {
        $url = $proto . $o_servername . $o_url;
    } else {
        $url = $proto . $o_servername . ':' . $o_url;
    }
} else {
    if (!defined($o_port)) {
        $url = $proto . $o_host . $o_url;
    } else {
        $url = $proto . $o_host . ':' . $o_port . $o_url;
    }
}
if (defined ($o_debug)) {
    print "\nDEBUG: HTTP url: \n";
    print $url;
}

my $req = HTTP::Request->new( GET => $url );

if (defined($o_servername)) {
    $req->header('Host' => $o_servername);
}
if (defined($o_user)) {
    $req->authorization_basic($o_user, $o_pass);
}

if (defined ($o_debug)) {
    print "\nDEBUG: HTTP request: \n";
    print "IP used (better if it's an IP):" . $override_ip . "\n";
    print $req->as_string;
}
$response = $ua->request($req);
my $timeelapsed = tv_interval ($timing0, [gettimeofday]);

my $InfoData = '';
my $PerfData = '';
#my @Time = (localtime); # list context and not scalar as we want the brutal timestamp
my $Time = time;

my $webcontent = undef;
if ($response->is_success) {
    $webcontent=$response->decoded_content;
    if (defined ($o_debug)) {
        print "\nDEBUG: HTTP response:";
        print $response->status_line;
        print "\n".$response->header('Content-Type');
        print "\n";
        print $webcontent;
    }
    if ($response->header('Content-Type') =~ m/text\/html/) {
        nagios_exit($check,"CRITICAL", "We have a response page for our request, but it's an HTML page, quite certainly not the status report of laborange");
    }
    # example of response content expected:
    #total_nodes=553
    #published_nodes=464
    #total_users=40761
    #enabled_users=1375
    #active_users=755
    #month_active_users=752
    #day_active_users=88
    #online_users=1
    #db_bootstrap=6ms
    #variables_bootstrap=40ms
    #node_article=19
    #node_content_list=1
    #node_documentation=17
    #node_dossier=3
    #node_editorial=17
    #node_fiche_application=2
    #node_forum=13
    #node_group=229
    #node_jalon=31
    #node_jeux_concours=1
    #node_list_participants=1
    #node_lot=61
    #node_mass_communication=1
    #node_module_agenda=2
    #node_module_liens=1
    #node_module_loterie=1
    #node_module_quiz=4
    #node_module_soumission=2
    #node_module_t_l_chargement=2
    #node_mur=2
    #node_page=10
    #node_project=12
    #node_salon_de_discussion=2
    #node_shop_product_display=3
    #node_slideshow=2
    #node_template=1
    #node_thread=11
    #node_thread_list=2
    #node_webform=11

    # activ conn
    my $ActiveConn = 0;
    if($webcontent =~ m/online_users=(.*?)\n/) {
        $ActiveConn = $1;
    }
    
    my $total_nodes=0;
    if($webcontent =~ m/total_nodes=(.*?)\n/) {
        $total_nodes = $1;
    }
    my $published_nodes=0;
    if($webcontent =~ m/published_nodes=(.*?)\n/) {
        $published_nodes = $1;
    }
    my $total_users=0;
    if($webcontent =~ m/total_users=(.*?)\n/) {
        $total_users = $1;
    }
    my $enabled_users=0;
    if($webcontent =~ m/enabled_users=(.*?)\n/) {
        $enabled_users = $1;
    }
    my $active_users=0;
    if($webcontent =~ m/active_users=(.*?)\n/) {
        $active_users = $1;
    }
    my $month_active_users=0;
    if($webcontent =~ m/month_active_users=(.*?)\n/) {
        $month_active_users = $1;
    }
    my $day_active_users=0;
    if($webcontent =~ m/day_active_users=(.*?)\n/) {
        $day_active_users = $1;
    }
    my $db_bootstrap=0;
    if($webcontent =~ m/db_bootstrap=(.*?)ms\n/) {
        $db_bootstrap = $1;
    }
    my $variables_bootstrap=0;
    if($webcontent =~ m/variables_bootstrap=(.*?)ms\n/) {
        $variables_bootstrap = $1;
    }
    my $node_article=0;
    if($webcontent =~ m/node_article=(.*?)\n/) {
        $node_article = $1;
    }
    my $node_documentation=0;
    if($webcontent =~ m/node_documentation=(.*?)\n/) {
        $node_documentation = $1;
    }
    my $node_editorial=0;
    if($webcontent =~ m/node_editorial=(.*?)\n/) {
        $node_editorial = $1;
    }
    my $node_group=0;
    if($webcontent =~ m/node_group=(.*?)\n/) {
        $node_group = $1;
    }
    my $node_jalon=0;
    if($webcontent =~ m/node_jalon=(.*?)\n/) {
        $node_jalon = $1;
    }
    my $node_lot=0;
    if($webcontent =~ m/node_lot=(.*?)\n/) {
        $node_lot = $1;
    }
    my $node_mass_communication=0;
    if($webcontent =~ m/node_mass_communication=(.*?)\n/) {
        $node_mass_communication = $1;
    }
    my $node_page=0;
    if($webcontent =~ m/node_page=(.*?)\n/) {
        $node_page = $1;
    }
    my $node_project=0;
    if($webcontent =~ m/node_project=(.*?)\n/) {
        $node_project = $1;
    }
    my $node_slideshow=0;
    if($webcontent =~ m/node_slideshow=(.*?)\n/) {
        $node_slideshow = $1;
    }
    my $node_webform=0;
    if($webcontent =~ m/node_webform=(.*?)\n/) {
        $node_webform = $1;
    }

    my $node_content_list=0;
    if($webcontent =~ m/node_content_list=(.*?)\n/) {
        $node_content_list = $1;
    }
    my $node_dossier=0;
    if($webcontent =~ m/node_dossier=(.*?)\n/) {
        $node_dossier = $1;
    }
    my $node_fiche_application=0;
    if($webcontent =~ m/node_fiche_application=(.*?)\n/) {
        $node_fiche_application = $1;
    }
    my $node_forum=0;
    if($webcontent =~ m/node_forum=(.*?)\n/) {
        $node_forum = $1;
    }
    my $node_jeux_concours=0;
    if($webcontent =~ m/node_jeux_concours=(.*?)\n/) {
        $node_jeux_concours = $1;
    }
    my $node_list_participants=0;
    if($webcontent =~ m/node_list_participants=(.*?)\n/) {
        $node_list_participants = $1;
    }
    my $node_module_agenda=0;
    if($webcontent =~ m/node_module_agenda=(.*?)\n/) {
        $node_module_agenda = $1;
    }
    my $node_module_liens=0;
    if($webcontent =~ m/node_module_liens=(.*?)\n/) {
        $node_module_liens= $1;
    }
    my $node_module_loterie=0;
    if($webcontent =~ m/node_module_loterie=(.*?)\n/) {
        $node_module_loterie = $1;
    }
    my $node_module_quiz=0;
    if($webcontent =~ m/node_module_quiz=(.*?)\n/) {
        $node_module_quiz = $1;
    }
    my $node_module_soumission=0;
    if($webcontent =~ m/node_module_soumission=(.*?)\n/) {
        $node_module_soumission = $1;
    }
    my $node_module_t_l_chargement=0;
    if($webcontent =~ m/node_module_t_l_chargement=(.*?)\n/) {
        $node_module_t_l_chargement = $1;
    }
    my $node_mur=0;
    if($webcontent =~ m/node_mur=(.*?)\n/) {
        $node_mur = $1;
    }
    my $node_salon_de_discussion=0;
    if($webcontent =~ m/node_salon_de_discussion=(.*?)\n/) {
        $node_webform = $1;
    }
    my $node_shop_product_display=0;
    if($webcontent =~ m/node_shop_product_display=(.*?)\n/) {
        $node_shop_product_display = $1;
    }
    my $node_template=0;
    if($webcontent =~ m/node_template=(.*?)\n/) {
        $node_template = $1;
    }
    my $node_thread=0;
    if($webcontent =~ m/node_thread=(.*?)\n/) {
        $node_thread = $1;
    }
    my $node_thread_list=0;
    if($webcontent =~ m/node_thread_list=(.*?)\n/) {
        $node_thread_list = $1;
    }
    $InfoData = sprintf (" %.3f sec. response time, Active: %d (day: %d month: %d all time: %d)"
                 . " Nodes: %d/%d Boot db: %d ms Boot vars: %d ms"
                 ,$timeelapsed,$ActiveConn,$day_active_users,$month_active_users,$active_users,$published_nodes,$total_nodes,$db_bootstrap,$variables_bootstrap);
    $PerfData = sprintf ("total_users=%d;enabled_users=%d;active_users=%d;month_active_users=%d;day_active_users=%d;online_users=%d;db_bootstrap=%d;variables_bootstrap=%d;total_nodes=%d;published_nodes=%d;node_article=%d;node_documentation=%d;node_editorial=%d;node_group=%d;node_jalon=%d;node_lot=%d;node_mass_communication=%d;node_page=%d;node_project=%d;node_slideshow=%d;node_webform=%d;node_content_list=%d;node_dossier=%d;node_fiche_application=%d;node_forum=%d;node_jeux_concours=%d;node_list_participants=%d;node_module_agenda=%d;node_module_liens=%d;node_module_loterie=%d;node_module_quiz=%d;node_module_soumission=%d;node_module_t_l_chargement=%d;node_mur=%d;node_salon_de_discussion=%d;node_shop_product_display=%d;node_template=%d;node_thread=%d;node_thread_list=%d"
                 ,($total_users),($enabled_users),($active_users),($month_active_users),($day_active_users),($ActiveConn),
                 ($db_bootstrap),($variables_bootstrap),($total_nodes),($published_nodes),($node_article),($node_documentation),
                 ($node_editorial),($node_group),($node_jalon),($node_lot),($node_mass_communication),($node_page),($node_project),
                 ($node_slideshow),($node_webform),($node_content_list),($node_dossier),($node_fiche_application),($node_forum),
                 ($node_jeux_concours),($node_list_participants),($node_module_agenda),($node_module_liens),($node_module_loterie),
                 ($node_module_quiz),($node_module_soumission),($node_module_t_l_chargement),($node_mur),($node_salon_de_discussion),
                 ($node_shop_product_display),($node_template),($node_thread),($node_thread_list));
    # first all critical exists by priority
    if (defined($o_crit_a_level) && (-1!=$o_crit_a_level) && ($ActiveConn >= $o_crit_a_level)) {
        nagios_exit($check,"CRITICAL", "Active Connections are critically high " . $InfoData,$PerfData);
    }
    # Then WARNING exits by priority
    if (defined($o_warn_a_level) && (-1!=$o_warn_a_level) && ($ActiveConn >= $o_warn_a_level)) {
        nagios_exit($check,"WARNING", "Active Connections are high " . $InfoData,$PerfData);
    }
    
    nagios_exit($check,"OK",$InfoData,$PerfData);

} else {
    nagios_exit($check,"CRITICAL", $response->status_line);
}
