#!/usr/bin/perl -w
# Author: Mark Foster
# (c) 2009 Credentia http://www.credentia.cc/
# $Id: check_zone.pl 104 2009-04-13 10:04:51Z mdf $
# Based on zonechk.pl, this script is a nagios plugin
#
# BUGS
# Not known
#
# TO DO
# ask each nameserver for the zones NS records, compare to authoritative list
# and warn once if any  mismatch found
# 
# REQUIREMENTS
# These perl modules
# Net::DNS (aptitude install libnet-dns-perl)
# Date::Calc (aptitude install libdate-calc-perl)
########################################################
use Date::Calc qw(Today_and_Now Delta_DHMS);
use Net::DNS ;
use Getopt::Long;
use strict(vars);

# Declare vars (strict requires this)
use vars qw($a $VERSION $debug @debug $thresholdWarns $thresholdCrits
 @reasons $arg @zones $localres $res $zone @rrset $rr $position
 $mismatch $nsrr $islame $position $a_query $soa_req $rcode
 $msg %arry %serial
);

my @a = split(/\s/, '$Id: check_zone.pl 104 2009-04-13 10:04:51Z mdf $'); #this will change on commit
$VERSION = $a[1]; undef(@a);

# Defaults
$thresholdWarns = 0;	
$thresholdCrits = 0;
$debug = 0;
@debug = (); # collector for debug output
$| = 1;
@reasons = ();

while ($arg = shift(@ARGV)) {
	if ($arg =~ /\-h|\-\-help/ ) { &usage; exit; }
	elsif ($arg =~ /\-w/) { $thresholdWarns = shift(@ARGV); }
	elsif ($arg =~ /\-c/) { $thresholdCrits = shift(@ARGV); }
	elsif ($arg =~ /\-v/) { $debug = 1; }
	elsif ($arg =~ /\-vv/) { $debug = 2; }
	else { push (@zones, $arg); }	
}

$res = new Net::DNS::Resolver;
$res->defnames(0);
$res->retry(1);
$res->tcp_timeout(7);
$res->udp_timeout(5);
$res->recurse(0); # don't recurse

$localres = new Net::DNS::Resolver; # Local resolver for resolving NS names to
# IP addresses (not something we can count on from the various other NS we talk
# to.
$localres->retry(1);
$localres->tcp_timeout(7);
$localres->udp_timeout(5);


foreach $zone (@zones) {
	&debug("BEGIN parsing of zone: ${zone}");
	# Look up the published DNS  servers (eg. what does the parent zone say)
   	my @auth_ns = (); # Authoritative Name servers according to top-down delegation
	my $sleep = 1; # starting point to back off retries upon query failures 
	my $this_ns = 'J.ROOT-SERVERS.NET'; # Got to start somewhere & J is close ;)
	$res->recurse(0); # do recurse to find right set of NS records
	my $fails = 0; my $authoritative = 0;	

	# Now iterate through the delegation path to find the answer to the
	# question: "Who is authoritative for this zone?"	
	while ((!$authoritative) && ($fails < 3)) { #keep asking til we get an authoritative answer
		&debug("Asking $this_ns for ${zone}'s SOA record");
		$res->nameservers($this_ns); # set nameserver we ask
		my $soa_req = $res->send($zone, "SOA"); # ask for SOA
		if(!$soa_req->header->aa) {
			if (defined($soa_req)) {
				if( $soa_req->authority ) {
					@rrset = $soa_req->authority;
					&debug("Reply = authority (delegation) from $this_ns");
					&debug("$this_ns delegates to " . $rrset[0]->nsdname ." as authoritative NS for $zone");
					$this_ns = $rrset[0]->nsdname;
				} else {
					&debug("Non AA & no authority (delegation) - bumping failure count");
					$fails++;	
				}
			}
		} else {
			&debug("Reply = answer (aa) from $this_ns");
			$authoritative = 1;	
			@rrset = $soa_req->authority;
			foreach $rr (@rrset) {
				push(@auth_ns,$rr->nsdname);
			}
		}

	}
	@{$zone} = @auth_ns;
	&debug("END parsing of zone: ${zone}");
}

# Now that we've assembled the list of nameservers for each zone, we'll check them individually
# for authoritative response and matching serials

my $totalErrs = 0; my $totalWarns = 0;

foreach $zone (@zones) {
	my $numErrs = 0; my $numWarns = 0;
	&debug("BEGIN checking serials for zone: $zone");
	$position = 0; #reset counter
	$mismatch=0; # reset mismatched NS indicator
	
	foreach $nsrr ( @{$zone} ) {
		$res = new Net::DNS::Resolver; # start fresh
		$islame = 0; 
		$position ++; #increment position...first will be our master
		$a_query = $localres->send($nsrr, "A"); # determine ip for this nsrr
		$res->nameservers($nsrr); # set nameserver we ask
		
		# if (position == 1) {
		# do any "per zone" checks here
		#}
		
		eval {
			$soa_req = $res->send($zone,"SOA"); # check the SOA for this zone

			&debug("Asking #$position nameserver $nsrr"); 
			# soa_req will be undefined on connection timeouts and the like
			if (defined($soa_req)) {
				if( $soa_req->answer ) {
					&debug( ($soa_req->answer)[0]->serial );
				} else {
					$msg = $res->errorstring;
					&debug( $msg );
					push(@reasons,"$msg");
					$islame = 1;
				}
			} else {
				&debug( $res->errorstring );
				push(@reasons,$res->errorstring);
				$islame = 1;
			}

			if ($a_query) {
				foreach $rr ($a_query->answer) {
					next unless $rr->type eq "A";
					$msg = $rr->type .':'. $rr->address;
					&debug( $msg );
				}
			} else {
				$msg = "$a_query failed";
				&debug( $msg );
				&debug( $res->errorstring );
				push(@reasons,"$msg");
				$islame = 1;
			}

			# bail now if the server was lame - always a problem
			if ($islame) {
				$msg = "$nsrr is LAME for $zone";
				&debug($msg);
				push(@reasons,"$msg");
				$numErrs++;
				next;
			}

			#Set serial if successful and it looks numeric
			if (($soa_req->answer)[0]->serial =~ /[0-9]/) { 
				$arry{$nsrr}{$zone} = ($soa_req->answer)[0]->serial;
			}
			if ( !$serial{$zone} ) {  # serial is undef
				$serial{$zone} = ($soa_req->answer)[0]->serial;
				&debug("good initial serial # found");
			} else { #Already primed our serial, check for mismatch or bump
				if ( ($serial{$zone} lt ($soa_req->answer)[0]->serial) 
				  && ( ($soa_req->answer)[0]->serial ne 0) 
				  && ( ($soa_req->answer)[0]->serial =~ /[0-9]/) 
				  && ( ($soa_req->answer)[0]->serial) ) { 
					&debug("higher serial # found");
					$serial{$zone} = ($soa_req->answer)[0]->serial; 
					$mismatch || $numWarns++; #bump warns if this is initial mismatch
					$mismatch = 1;
				}
				if ( ($serial{$zone} gt ($soa_req->answer)[0]->serial) ) {
					# It's smaller
					&debug("lower serial # found");
					$mismatch || $numWarns++; #bump warns if this is initial mismatch
					$mismatch=1;
				}
			}

			# but this condition is as good as lame IMO -mdf
			if(!$soa_req->header->aa) {
				$msg = "Non Authoritative Answer";
				$arry{$nsrr}{$zone} = $msg;
				&debug("$msg for $zone from $nsrr");
				push(@reasons,"$msg");
				$numWarns++;
			}

			elsif($soa_req->header->ancount != 1) {
				if ($arry{$zone}{$nsrr}) {
					$msg = "Multiple Answers Returned";
					$arry{$nsrr}{$zone} = $msg;
					&debug("$msg for $zone from $nsrr");
					push(@reasons,"$msg");
					$numWarns++;
				}
			}
		} # End eval
	} 

	if ($serial{$zone}) { &debug("Highest serial# for $zone is $serial{$zone}");  
		&debug("Mismatched serials: $mismatch for zone $zone");
	} else { 
		$msg = "Serial# unknown for zone $zone";
		&debug("$msg - zone is badly broken");
		push(@reasons,"$msg");
		$numErrs++; 
	}
	&debug("Errors: $numErrs, Warns: $numWarns");
	$totalErrs += $numErrs;
	$totalWarns += $numWarns;
	&debug("END checking serials for zone: $zone");
}



# Evaluate and do output
if (($totalErrs <= $thresholdCrits) && ($totalWarns <= $thresholdWarns)) {
	print "OK "; $rcode = 0;
} elsif ($totalErrs > $thresholdCrits) {
	print "CRITICAL "; $rcode = 2;
} elsif ($totalWarns > $thresholdWarns) {
	print "WARNING "; $rcode = 1;
} else {
	print "UNKNOWN "; $rcode = 3;
}
print "Errors:$totalErrs Warns:$totalWarns";
if ($rcode != 0) {
	print " Reasons:", join(";", @reasons);
}
print "\n";

if ($debug) { print "DEBUG:", join("\nDEBUG:", @debug), "\n\n"; }

exit $rcode;

# Subroutines 
sub usage {
	print <<EOF;
Usage: $0 [-d] domain <2nddomain>...
Where domain is the apex of a zone
EOF

}

sub debug { 
 	$_ = shift;
	if ($debug eq "2") {
		print "DEBUG: $_\n";
	}
	push(@debug, $_);
}



