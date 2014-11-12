#!/usr/bin/perl -w
# nagios: -epn

#######################################################
#                                                     #
#  Name:    check_io                                  #
#                                                     #
#  Version: 0.5                                       #
#  Created: 2012-12-13                                #
#  License: GPL - http://www.gnu.org/licenses         #
#  Copyright: (c)2012-2013 ovido gmbh                 #
#             (c)2014 Rene Koch <rkoch@linuxland.at>  #
#  Author:  Rene Koch <r.koch@ovido.at>               #
#  Credits: s IT Solutions AT Spardat GmbH            #
#  URL: https://github.com/ovido/check_io             #
#                                                     #
#######################################################

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Changelog:
# * 0.5.0 - Wed Jul 16 2014 - Rene Koch <rkoch@linuxland.at>
# - Fixed regex for Solaris md devices
# * 0.4.0 - Wed Apr 16 2014 - Rene Koch <rkoch@linuxland.at>
# - Fixed regex for RHEL 4 support (thanks nenioscio)
# * 0.3.0 - Mon Jan 14 2013 - Rene Koch <r.koch@ovido.at>
# - Added %b (Solaris) and $util (Linux) checks
# * 0.2.0 - Mon Dec 17 2012 - Rene Koch <r.koch@ovido.at>
# - Added short names for Solaris disks
# * 0.1.0 - Thu Dec 12 2012 - Rene Koch <r.koch@ovido.at>
# - This is the first public beta release of new plugin check_io

use strict;
use Getopt::Long;
use List::Util qw( min max sum );

# Configuration
my $tmp_errors = "/var/tmp/check_io_";
my $o_runs	= 5;		# iostat runs
my $o_interval	= 1;		# iostat interval

# create performance data
# 0 ... disabled
# 1 ... enabled
my $perfdata	= 1;

# Variables
my $prog	= "check_io";
my $version	= "0.5";
my $projecturl  = "https://github.com/ovido/check_io";

my $o_verbose	= undef;	# verbosity
my $o_help	= undef;	# help
my $o_version	= undef;	# version
my @o_exclude	= ();		# exclude disks
my $o_errors	= undef;	# error detection
my $o_short	= undef;	# short names for disks
my $o_max	= undef;	# get max values
my $o_average	= undef;	# get average values
my $o_warn	= undef;	# warning
my $o_crit	= undef;	# critical
my @warn	= ();
my @crit	= ();

my %status	= ( ok => "OK", warning => "WARNING", critical => "CRITICAL", unknown => "UNKNOWN");
my %ERRORS	= ( "OK" => 0, "WARNING" => 1, "CRITICAL" => 2, "UNKNOWN" => 3);

my $statuscode	= "unknown";
my $statustext	= "";
my $perfstats	= "|";
my %errors;

#***************************************************#
#  Function: parse_options                          #
#---------------------------------------------------#
#  parse command line parameters                    #
#                                                   #
#***************************************************#
sub parse_options(){
  Getopt::Long::Configure ("bundling");
  GetOptions(
	'v+'	=> \$o_verbose,		'verbose+'	=> \$o_verbose,
	'h'	=> \$o_help,		'help'		=> \$o_help,
	'V'	=> \$o_version,		'version'	=> \$o_version,
	'r:i'	=> \$o_runs,		'runs:i'	=> \$o_runs,
	'i:i'	=> \$o_interval,	'interval:i'	=> \$o_interval,
	'e:s'	=> \@o_exclude,		'exclude:s'	=> \@o_exclude,
	'E'	=> \$o_errors,		'errors'	=> \$o_errors,
	's'	=> \$o_short,		'short'		=> \$o_short,
	'm'	=> \$o_max,		'max'		=> \$o_max,
	'a'	=> \$o_average,		'average'	=> \$o_average,
	'w:s'	=> \$o_warn,		'warning:s'	=> \$o_warn,
	'c:s'	=> \$o_crit,		'critical:s'	=> \$o_crit
  );

  # process options
  print_help()		if defined $o_help;
  print_version()	if defined $o_version;

  # can't use max and average
  if (defined $o_max && defined $o_average){
    print "Can't use max and average at the same time!\n";
    print_usage();
    exit $ERRORS{$status{'unknown'}};
  }

  if ((! defined $o_warn) || (! defined $o_crit)){
    print "Warning and critical values are required!\n";
    print_usage();
    exit $ERRORS{$status{'unknown'}};
  }

  # check warning and critical
  if ($o_warn !~ /^(\d+)(\.?\d+)*,{1}(\d+)(\.?\d+)*,(\d+)(\.?\d+)*,(\d+)(\.?\d+)*$/){
    print "Please give proper warning values!\n";
    print_usage();
    exit $ERRORS{$status{'unknown'}};
  }else{
    @warn = split /,/, $o_warn;
  }

  if ($o_crit !~ /^(\d+)(\.?\d+)*,{1}(\d+)(\.?\d+)*,(\d+)(\.?\d+)*,(\d+)(\.?\d+)*$/){
    print "Please give proper critical values!\n";
    print_usage();
    exit $ERRORS{$status{'unknown'}};
  }else{
    @crit = split /,/, $o_crit;
  }

  # verbose handling
  $o_verbose = 0 if ! defined $o_verbose;

}


#***************************************************#
#  Function: print_usage                            #
#---------------------------------------------------#
#  print usage information                          #
#                                                   #
#***************************************************#
sub print_usage(){
  print "Usage: $0 [-v] [-r <runs>] [-i <interval>] [-e <exclude>] [-E] [-s] [-m|-a] \n";
  print "        -w <tps,svctm,wait,util> -c <tps,svctm,wait,util>\n";
}


#***************************************************#
#  Function: print_help                             #
#---------------------------------------------------#
#  print help text                                  #
#                                                   #
#***************************************************#
sub print_help(){
  print "\nLinux and Solaris I/O checks for Icinga/Nagios version $version\n";
  print "GPL license, (c)2012 - Rene Koch <r.koch\@ovido.at>\n\n";
  print_usage();
  print <<EOT;

Options:
 -h, --help
    Print detailed help screen
 -V, --version
    Print version information
 -r, --runs=INTEGER
    iostat count (default: $o_runs)
 -i, --interval=INTEGER
    iostat interval (default: $o_interval)
 -e, --exclude=REGEX
    Regex to exclude disks from beeing checked
 -E, --errors
    Check disk errors on Solaris
 -s, --short
    Use short names on Solaris for Perfdata
 -m, --max
    Use max. values of runs for tps, svctm iowait and util (default)
 -a, --average
    Use average values of runs for tps, svctm iowait and util
 -w, --warning=<tpd,svctm,wait,util>
    Value to result in warning status
    tps: transfers per second
    svctm: avg service time for I/O requests issued to the device
    wait: CPU I/O waiting for outstanding I/O requests
    util: ercentage of CPU time during which requests were issued
 -c, --critical=<tpd,svctm,wait,util>
    Value to result in critical status
    tps: transfers per second
    svctm: avg service time for I/O requests issued to the device
    wait: CPU I/O waiting for outstanding I/O requests
    util: ercentage of CPU time during which requests were issued
 -v, --verbose
    Show details for command-line debugging
    (Icinga/Nagios may truncate output)

Send email to r.koch\@ovido.at if you have questions regarding use
of this software. To submit patches of suggest improvements, send
email to r.koch\@ovido.at
EOT

exit $ERRORS{$status{'unknown'}};
}



#***************************************************#
#  Function: print_version                          #
#---------------------------------------------------#
#  Display version of plugin and exit.              #
#                                                   #
#***************************************************#

sub print_version{
  print "$prog $version\n";
  exit $ERRORS{$status{'unknown'}};
}


#***************************************************#
#  Function: main                                   #
#---------------------------------------------------#
#  The main program starts here.                    #
#                                                   #
#***************************************************#

# parse command line options
parse_options();

# get operating system
my $kernel_name = `uname -s`;
my $kernel_release = `uname -r | cut -d- -f1`;
chomp $kernel_name;
chomp $kernel_release;

my $cmd = undef;
my $devices = "";

if ($kernel_name eq "Linux"){

  # get list of devices
  my @tmp = `iostat -d`;
  for (my $i=0;$i<=$#tmp;$i++){
    next if $tmp[$i] =~ /^$/;
    next if $tmp[$i] =~ /^Linux/;
    next if $tmp[$i] =~ /^Device:/;
    chomp $tmp[$i];
    my @dev = split / /, $tmp[$i];

    # match devs with exclude list
    my $match = 0;
    for (my $x=0;$x<=$#o_exclude;$x++){
      $match = 1 if $dev[0] =~ /$o_exclude[$x]/;
    }

    # exclude cd drives
    if (-e "/dev/cdrom"){
      my $cdrom = `ls -l /dev/cdrom | tr -s ' ' ' ' | cut -d' ' -f11`;
      chomp $cdrom;
      next if $dev[0] eq $cdrom;
    }

    $devices .= " " . $dev[0] if $match != 1;

  }

  $cmd = "iostat -kx" . $devices . " " . $o_interval . " " . $o_runs;

}elsif ($kernel_name eq "SunOS"){

    $devices = "";
    my @tmp = `iostat -xn`;
    for (my $i=0;$i<=$#tmp;$i++){
      next if $tmp[$i] =~ /^$/;
      next if $tmp[$i] =~ /^(\s+)extended(\s)device(\s)statistics/;
      next if $tmp[$i] =~ /^(\s+)r\/s(\s+)w\/s(\s+)kr\/s/;
      chomp $tmp[$i];
      $tmp[$i] =~ s/\s+/ /g;
      my @dev = split / /, $tmp[$i];

      # match devs with exclude list
      my $match = 0;
      for (my $x=0;$x<=$#o_exclude;$x++){
	$match = 1 if $dev[11] =~ /$o_exclude[$x]/;
      }

      # exclude cd drives
      if (-e "/dev/sr0"){
	my $cdrom = `ls -l /dev/sr0 | tr -s ' ' ' ' | cut -d' ' -f11 | cut -d/ -f2`;
        chop $cdrom;
        chop $cdrom;
        chop $cdrom;
	next if $dev[11] eq $cdrom;
      }

      # skip automount devices
      next if $dev[11] =~ /vold\(pid\d+\)/;
      
      # fix name for md devices
      # e.g. 2.5    6.1   68.6  118.4  0.0  0.0    0.0    1.8   0   1 2/md13
      if ($dev[11] =~ /^(\d+)\/(\w+)/){
      	$dev[11] =~ s/^(\d+)\///;
      }

      $devices .= " " . $dev[11] if $match != 1;

      # handle temp files for disk
      if (defined $o_errors){
        if (! -e $tmp_errors . "_" . $dev[11]){
          if (! open (TMPERRORS, ">$tmp_errors" . "_" . $dev[11]) ){
	    print "File $tmp_errors isn't writeable!\n";
	    exit $ERRORS{$status{'unknown'}};
          }
          # fill file with 0 values
          my @a = ("soft","hard","transport","media","drive","nodev","recoverable","illegal");
	  foreach (@a){
	    print TMPERRORS $_ . " 0\n";
	    $errors{$dev[11]}{$_} = 0;
	  }
          close (TMPERRORS);
        }else{
          if (! -w $tmp_errors . "_" . $dev[11]){
	    print "File $tmp_errors isn't writeable!\n";
	    exit $ERRORS{$status{'unknown'}};
          }
          # read values
          open TMPERRORS, $tmp_errors . "_" . $dev[11];
          while (<TMPERRORS>){
	    my @tmp = split / /, $_;
	    $errors{$dev[11]}{$tmp[0]} = $tmp[1];
          }
          close (TMPERRORS);
        }
      }

    }
    if (defined $o_errors){
      $cmd = "iostat -Excn" . $devices . " " . $o_interval . " " . $o_runs;
    }else{
      $cmd = "iostat -xcn" . $devices . " " . $o_interval . " " . $o_runs;
    }

}else{
  exit_plugin ("unknown", "Operating system $kernel_name isn't supported, yet.");
}

my %iostat;
my $x=0;
my $hdd = undef;

# get statistics from iostat
my @result = `$cmd`;
for (my $i=0;$i<=$#result;$i++){

  $result[$i] =~ s/\s+/ /g;

  # Fedora / RHEL:
  # Linux 3.4.11-1.fc16.x86_64 (pc-ovido02.lan.ovido.at) 	12/11/2012 	_x86_64_	(4 CPU)
  #
  # avg-cpu:  %user   %nice %system %iowait  %steal   %idle
  #            6.15    0.00    2.94    1.93    0.00   88.98
  #
  # Device:         rrqm/s   wrqm/s     r/s     w/s    rkB/s    wkB/s avgrq-sz avgqu-sz   await r_await w_await  svctm  %util
  # sda               0.40    10.24    3.41   13.54    70.65   103.22    20.52     0.26   15.27   13.18   15.80   4.41   7.47

  # Solaris:
  #     cpu
  # us sy wt id
  #  1  1  0 98
  #                    extended device statistics              
  #    r/s    w/s   kr/s   kw/s wait actv wsvc_t asvc_t  %w  %b device
  #    0.3    1.6   15.8   12.0  0.0  0.0    5.0    3.2   0   0 c0d0

  # get disk statistics on Linux
  if ( $result[$i] =~ /^(\w+)(-*)(\d*)(\s)((\d+)\.(\d+)(\s){1}){5}(\d+)\.(\d+)/ ){

    my @tmp = split / /, $result[$i];
    $iostat{$tmp[0]}{'rs'}[$x-1] = $tmp[3];
    $iostat{$tmp[0]}{'ws'}[$x-1] = $tmp[4];
    $iostat{$tmp[0]}{'rkBs'}[$x-1] = $tmp[5];
    $iostat{$tmp[0]}{'wkBs'}[$x-1] = $tmp[6];
    $iostat{$tmp[0]}{'wait'}[$x-1] = $tmp[9];
    if (! $tmp[12]){
      $iostat{$tmp[0]}{'svctm'}[$x-1] = $tmp[10];
      $iostat{$tmp[0]}{'util'}[$x-1] = $tmp[11];
    }else{
      $iostat{$tmp[0]}{'svctm'}[$x-1] = $tmp[12];
      $iostat{$tmp[0]}{'util'}[$x-1] = $tmp[13];
    }

  # get disk statistics on Solaris
  }elsif ( $result[$i] =~ /^(\s+)((\d+)\.(\d+)(\s){1}){8}((\d+)(\s){1}){2}(\w+)/ ){

    my @tmp = split / /, $result[$i];
    $iostat{$tmp[11]}{'rs'}[$x-1] = $tmp[1];
    $iostat{$tmp[11]}{'ws'}[$x-1] = $tmp[2];
    $iostat{$tmp[11]}{'rkBs'}[$x-1] = $tmp[3];
    $iostat{$tmp[11]}{'wkBs'}[$x-1] = $tmp[4];
    $iostat{$tmp[11]}{'wait'}[$x-1] = $tmp[5];
    $iostat{$tmp[11]}{'svctm'}[$x-1] = $tmp[7] + $tmp[8];
    $iostat{$tmp[11]}{'util'}[$x-1] = $tmp[10];

  # get ioawait on Linux
  }elsif ( $result[$i] =~ /^(\s){1}((\d){1,3}\.(\d){1,2}(\s){1}){4,5}(\d){1,3}\.(\d){1,2}(\s){1}$/ ){

    my @tmp = split / /, $result[$i];
    $iostat{'iowait'}[$x] = $tmp[4];
    $x++;

  # get iowait on Solaris
  }elsif ( $result[$i] =~ /^(\s){1}((\d){1,3}(\s){1}){3}(\d){1,3}(\s){1}$/ ){

    my @tmp = split / /, $result[$i];
    $iostat{'iowait'}[$x] = $tmp[3];
    $x++;

  # get disks errors on Solaris
  }elsif ( $result[$i] =~ /Soft\sErrors:/ ){
    my @tmp = split / /, $result[$i];
    $hdd = $tmp[0];
    if ($tmp[3] > $errors{$hdd}{'soft'}){
      $statuscode = "critical";
      $statustext .= " $hdd (Soft Errors: $tmp[3])";
    }
    if ($tmp[6] > $errors{$hdd}{'hard'}){
      $statuscode = "critical";
      $statustext .= " $hdd (Hard Errors: $tmp[6])";
    }
    if ($tmp[9] > $errors{$hdd}{'transport'}){
      $statuscode = "critical";
      $statustext .= " $hdd (Transport Errors: $tmp[9])";
    }
    $errors{$hdd}{'soft'} = $tmp[3];
    $errors{$hdd}{'hard'} = $tmp[6];
    $errors{$hdd}{'transport'} = $tmp[9];
  }elsif ( $result[$i] =~ /^Media\sError:/ ){
    my @tmp = split / /, $result[$i];
    if ($tmp[2] > $errors{$hdd}{'media'}){
      $statuscode = "critical";
      $statustext .= " $hdd (Media Errors: $tmp[2])";
    }
    if ($tmp[6] > $errors{$hdd}{'drive'}){
      $statuscode = "critical";
      $statustext .= " $hdd (Drive Not Ready: $tmp[6])";
    }
    if ($tmp[9] > $errors{$hdd}{'nodev'}){
      $statuscode = "critical";
      $statustext .= " $hdd (No Device: $tmp[9])";
    }
    if ($tmp[11] > $errors{$hdd}{'recoverable'}){
      $statuscode = "warning" if $statuscode ne "critical";
      $statustext .= " $hdd (Recoverable: $tmp[11])";
    }
    $errors{$hdd}{'media'} = $tmp[2];
    $errors{$hdd}{'drive'} = $tmp[6];
    $errors{$hdd}{'nodev'} = $tmp[9];
    $errors{$hdd}{'recoverable'} = $tmp[11];
  }elsif ( $result[$i] =~ /^Illegal\sRequest:/ ){
    my @tmp = split / /, $result[$i];
    if ($tmp[2] > $errors{$hdd}{'illegal'}){
      $statuscode = "critical";
      $statustext .= " $hdd (Illegal Requests: $tmp[2])";
    }
    $errors{$hdd}{'illegal'} = $tmp[2];
   }
}

if (defined $o_errors){
  foreach my $disk (keys %errors){
    # write errors to file
    if (! open (TMPERRORS, ">$tmp_errors" . "_" . $disk) ){
      print "File $tmp_errors" . "_" . "$disk isn't writeable!\n";
      exit $ERRORS{$status{'unknown'}};
    }
    foreach my $param (keys %{ $errors{$disk} }){
      print TMPERRORS $param . " $errors{$disk}{$param}\n";
      $perfstats .= "'" . $disk . "_" . $param . "'=$errors{$disk}{$param}c;;;0; ";
    }
    close (TMPERRORS);
  }
}


# do some calculations

# iowait
my $value = undef;
$value = max @{ $iostat{'iowait'} } if defined $o_max;
$value = (sum @{ $iostat{'iowait'} }) / (scalar @{ $iostat{'iowait'} }) if ! defined $o_max;
$perfstats .= "'iowait'=$value%;$warn[2];$crit[2];0;100 ";

if ($value >= $crit[2]){
  $statuscode = 'critical';
  $statustext .= " iowait: $value,";
}elsif ($value >= $warn[2]){
  $statuscode = 'warning';
  $statustext .= " iowait: $value," if $statuscode ne 'critical';
  $statustext .= " iowait: $value," if $o_verbose >= 1 && $statuscode eq 'critical';
}else{
  $statuscode = 'ok' if $statuscode ne 'critical' && $statuscode ne 'warning';
  $statustext .= " iowait: $value," if $o_verbose >= 1;
}


# disk statistics
foreach my $disk (keys %iostat){
  my $io = undef;
  my $tmp_sc = undef;
  next if $disk eq 'iowait';
  my ($rs, $ws) = undef;
  my %output;
  foreach my $param (keys %{ $iostat{$disk} }){
    # remove first entry when using multiple runs
    shift @{ $iostat{$disk}{$param} } if $o_runs > 1;
    $value = max @{ $iostat{$disk}{$param} } if defined $o_max;
    $value = (sum @{ $iostat{$disk}{$param} }) / (scalar @{ $iostat{$disk}{$param} }) if ! defined $o_max;
    if ($param eq "rs"){
      $rs = $value;
      $perfstats .= "'" . $disk . "_r/s'=$value;$warn[0];$crit[0];0; ";
    }elsif ($param eq "ws"){
      $ws = $value;
      $perfstats .= "'" . $disk . "_w/s'=$value;$warn[0];$crit[0];0; ";
    }elsif ($param eq "rkBs"){
      $perfstats .= "'" . $disk . "_rkB/s'=$value" . "KB;;;0; ";
    }elsif ($param eq "wkBs"){
      $perfstats .= "'" . $disk . "_wkB/s'=$value" . "KB;;;0; ";
    }elsif ($param eq "wait"){
      $perfstats .= "'" . $disk . "_wait'=$value" . "ms;;;0; ";
    }elsif ($param eq "svctm"){
      ($statuscode,$tmp_sc) = get_status($value,$warn[1],$crit[1]);
      $output{$disk}{$param} = $value if ( ($tmp_sc eq 'critical') || ($tmp_sc eq 'warning') );
      $io .= ", $param $value" if $o_verbose >= 1;
      $perfstats .= "'" . $disk . "_svctm'=$value;$warn[1];$crit[1];0; ";
    }elsif ($param eq "util"){
      ($statuscode,$tmp_sc) = get_status($value,$warn[3],$crit[3]);
      $output{$disk}{$param} = $value if ( ($tmp_sc eq 'critical') || ($tmp_sc eq 'warning') );
      $io = " $disk (util $value" if $o_verbose >= 1;
      $perfstats .= "'" . $disk . "_util'=$value" . "%;;;0; ";
    }
  }
  my $tps = $rs + $ws;
  ($statuscode,$tmp_sc) = get_status($tps,$warn[0],$crit[0]);
  $io .= ", tps $tps)" if $o_verbose >= 1;
  $output{$disk}{'tps'} = $tps if ( ($tmp_sc eq 'critical') || ($tmp_sc eq 'warning') );
  
  if (defined $io){
    $statustext .= $io;
  }else{
    # print warning and critical values per disk
    foreach my $dsk (keys %output){
      $statustext .= " $disk (";
      foreach my $parm (keys %{ $output{$dsk} }){
        $statustext .= "$parm $output{$dsk}{$parm}, ";
      }
      chop $statustext;
      chop $statustext;
      $statustext .= ")";
    }
  }
}

$statustext = " on all disks." if $statuscode eq 'ok' && $o_verbose == 0;
# add checked devices to statustext
$statustext .= " [disks:$devices]";

# loop through format to get disk numbers
if (defined $o_short && $kernel_name eq "SunOS"){

# get devices 
my @devs = `echo | format`;
  for (my $i=0;$i<=$#devs;$i++){
    $devs[$i] =~ s/\s+/ /g;
    next if $devs[$i] !~ /^(\s){1}(\d){1,3}\.(\s){1}(\w+)/;
    chomp $devs[$i];
    my @dev = split / /, $devs[$i];
    chop $dev[1];
    # substitute disk names with disk number from format - e.g.
    # d0: c0t0d0
    # d14: c10t60060160B0902800B6CDAB49CD57DF11d0
    $perfstats =~ s/$dev[2]/d$dev[1]/g if $perfstats =~ $dev[2];
  }

}

$statustext .= $perfstats if $perfdata == 1;
exit_plugin($statuscode,$statustext);


#***************************************************#
#  Function get_status                              #
#---------------------------------------------------#
#  Matches value againts warning and critical       #
#  ARG1: value                                      #
#  ARG2: warning                                    #
#  ARG3: critical                                   #
#***************************************************#

sub get_status{
  my $tmp_sc = undef;
  if ($_[0] >= $_[2]){
    $statuscode = 'critical';
    $tmp_sc = 'critical';
  }elsif ($_[0] >= $_[1]){
    $statuscode = 'warning' if $statuscode ne 'critical';
    $tmp_sc = 'warning';
  }else{
    $statuscode = 'ok' if $statuscode ne 'critical' && $statuscode ne 'warning';
    $tmp_sc = 'ok';
  }
  return ($statuscode,$tmp_sc);
}

#***************************************************#
#  Function exit_plugin                             #
#---------------------------------------------------#
#  Prints plugin output and exits with exit code.   #
#  ARG1: status code (ok|warning|cirtical|unknown)  #
#  ARG2: additional information                     #
#***************************************************#

sub exit_plugin{
  print "I/O $status{$_[0]}:$_[1]\n";
  exit $ERRORS{$status{$_[0]}};
}


exit $ERRORS{$status{'unknown'}};

