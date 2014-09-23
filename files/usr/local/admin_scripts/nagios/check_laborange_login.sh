#!/bin/bash

# GNU GPL v3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

PROGRAM="check_laborange_login";
VERSION="0.2";
AUTHOR="Régis Leroy regis.leroy@makina-corpus.com";
NICK="LOGINLAB"
OK=0;
WARNING=1;
CRITICAL=2;
UNKNOWN=3;
PENDING=4;

print_version() {
    echo $PROGRAM
    echo "Version: $VERSION Author: $AUTHOR";
    echo "-------------------------------------------------------------------------------------"
}

print_help() {
    print_version
    echo "";
    echo "$PROGRAM : Check we can connect with a user login on Lab'Orange";
    echo "";
    print_usage
}

print_usage() {
    echo "USAGE: $PROGRAM [OPTIONS]";
    echo;
    echo "-h|--help     : show program help";
    echo "-v|--version  : show program version";
    echo "-u            : Host url (full with http://)";
    echo "-a            : HTTP Auth pair user";
    echo "-p            : HTTP Auth pair password";
    echo "-c            : Critical thresold (default 10)";
    echo "-w            : Warning thresold (default 5)";
    echo "";
    echo "Thresolds are computed in seconds on the time needed to load home page after login.";
    echo "Bad login will always be critical.";
}
#Default
URL="http://dev.laborange.com"

LOGIN="monitoring"
PASSWORD="RuedCiWruj1"
# To check in resulting page content
USERNAME="monitoring"

COOKIE="/tmp/nagios_laborange_conn_cookie.txt"
BODY="/tmp/nagios_laborange_conn_page-content.txt"
BODYSHOP="/tmp/nagios_laborange_conn_page-contentshop.txt"
BODYFAILURE="/tmp/nagios_laborange_conn_page-content-failure.txt"
BODYSHOPFAILURE="/tmp/nagios_laborange_conn_page-contentshop-failure.txt"
CTHRESOLD=10
WTHRESOLD=5
# Parse args
ARGS=`getopt vhc:w:u:a:p: $*`;
while test -n "$1"; do
    case "$1" in
      --help|-h)
          shift;
          print_help;
          exit $UNKNOWN;
      ;;
      --version|-v)
          shift;
          print_version ;
          exit $UNKNOWN;
      ;;
      -u)
          shift;
          URL=$1;
          shift;
      ;;
      -a)
          shift;
          AUTHUSER=$1;
          shift;
      ;;
      -p)
          shift;
          AUTHPASSWORD=$1;
          shift;
      ;;
      -c)
          shift;
          CTHRESOLD=$1;
          shift;
      ;;
      -w)
          shift;
          WTHRESOLD=$1;
          shift;
      ;;
      *)
          echo 
          echo "====================================="
          echo "$NICK UNKNOWN - Unknown argument: $1";
          echo "====================================="
          echo
          print_help;
          exit $UNKNOWN;
      ;;
    esac;
done

# Check tools
WGET=`which wget`;
if [ ! ${WGET} ]; then
  echo "$NICK UNKNOWN - You do not have the wget utility?"
  exit $UNKNOWN
fi

GREP=`which grep`;
if [ ! ${GREP} ]; then
  echo "$NICK UNKNOWN - You do not have the grep utility?"
  exit $UNKNOWN
fi

TR=`which tr`;
if [ ! ${TR} ]; then
  echo "$NICK UNKNOWN - You do not have the tr utility?"
  exit $UNKNOWN
fi

CUT=`which cut`;
if [ ! ${CUT} ]; then
  echo "$NICK UNKNOWN - You do not have the cut utility?"
  exit $UNKNOWN
fi

SED=`which sed`;
if [ ! ${SED} ]; then
  echo "$NICK UNKNOWN - You do not have the sed utility?"
  exit $UNKNOWN
fi

if [ ${AUTHUSER} ]; then
  WGET="${WGET} --user=${AUTHUSER} --password=${AUTHPASSWORD}"
fi

# Build urls & commands
LOGIN_URL=${URL}"/home";
HOME_URL=${URL}"/home";
SHOP_BASEURL=`echo ${URL} | sed 's_http://_http://boutique._'`;
SHOP_URL=${SHOP_BASEURL}"/";
LOGOUT_URL=${URL}"/user/logout"
POST_LOGIN_URL=${URL}"/home?destination=home"

# 1st page command
COMMAND1="${WGET} -q --cookies=on --keep-session-cookies --save-cookies=${COOKIE} -O ${BODY} ${LOGIN_URL}"

# COMMAND2 is the login POST command, build later as we need to extract some content from COMMAND1 result

# After login post page GET command
COMMAND3="${WGET} -q --cookies=on --keep-session-cookies --load-cookies=${COOKIE} --save-cookies=${COOKIE} --referer=${LOGIN_URL} -O ${BODY} ${HOME_URL}"

# Same as After login post page GET command  but with another save file (record failure)
COMMAND3BIS="${WGET} -q --cookies=on --keep-session-cookies --load-cookies=${COOKIE} --save-cookies=${COOKIE} --referer=${LOGIN_URL} -O ${BODYFAILURE} ${HOME_URL}"

# Shop GET command
COMMAND4="${WGET} -q --cookies=on --keep-session-cookies --load-cookies=${COOKIE} --save-cookies=${COOKIE} --referer=${HOME_URL} -O ${BODYSHOP} ${SHOP_URL}"

# Same as SHOP GET command but with another save file (record failure)
COMMAND4BIS="${WGET} -q --cookies=on --keep-session-cookies --load-cookies=${COOKIE} --save-cookies=${COOKIE} --referer=${HOME_URL} -O ${BODYSHOPFAILURE} ${SHOP_URL}"

# Logout command
COMMAND5="${WGET} -q --cookies=on --keep-session-cookies --load-cookies=${COOKIE} --save-cookies=${COOKIE} --referer=${HOME_URL} -O - ${LOGOUT_URL}"

# Let's go ########################################################

# Empty cookies and old files
rm -f ${COOKIE};
rm -f ${BODY};
rm -f ${BODYSHOP};
rm -f ${BODYFAILURE};
rm -f ${BODYSHOPFAILURE};

# @see http://serverfault.com/questions/151109/how-do-i-get-current-unix-time-in-milliseconds-using-bash
TIMESTART=`date +%s%N|${CUT} -b1-13`;
# get login page ###############
# store result in BODY file ####
#echo ${COMMAND1};
${COMMAND1} >/dev/null;
TIMEINIT=`date +%s%N|${CUT} -b1-13`;
FORMID=`${GREP} -B1 "name=\"form_id\" value=\"user_login_block\"" ${BODY}|${GREP} "form_build_id"|${TR} -s " " |${CUT} -d "=" -f 4|${CUT} -d "\"" -f 2`;
#echo $FORMID

# Post login form ##############
POSTDATA="name=${LOGIN}&pass=${PASSWORD}&form_id=user_login_block&op=Se+connecter&form_build_id=${FORMID}"
COMMAND2="${WGET} -q -O - --cookies=on --keep-session-cookies --load-cookies=${COOKIE} --save-cookies=${COOKIE} --referer=${LOGIN_URL} --post-data=${POSTDATA} ${POST_LOGIN_URL}"
#echo ${COMMAND2};
${COMMAND2} >/dev/null;
TIMELOG=`date +%s%N|${CUT} -b1-13`;

# Take the HOME redirect #######
# store result in BODY file ####
#echo ${COMMAND3};
${COMMAND3} >/dev/null;
TIMEEND=`date +%s%N|${CUT} -b1-13`;

# Visit Shop #######################
# store result in BODYSHOP file ####
#echo ${COMMAND4};
${COMMAND4} >/dev/null;
TIMESHOP=`date +%s%N|${CUT} -b1-13`;

# Logout #######################
#echo ${COMMAND5}
${COMMAND5} >/dev/null;

# Visit Shop again (failure) ##############
# store result in BODYSHOPFAILURE file ####
#echo ${COMMAND4BIS};
${COMMAND4BIS} >/dev/null;

# Visit portal again (failure) ########
# store result in BODYFAILURE file ####
#echo ${COMMAND3BIS};
${COMMAND3BIS} >/dev/null;

((TIMEFIRST= ${TIMEINIT}-${TIMESTART}));
((TIMELOGIN=${TIMELOG}-${TIMEINIT}));
((TIMEUSER=${TIMEEND}-${TIMEINIT}));
((TIMECONNECTED=${TIMEEND}-${TIMELOG}));
((TIMELOADSHOP=${TIMESHOP}-${TIMEEND}));
let CTHRESOLDMS=${CTHRESOLD}*1000;
let WTHRESOLDMS=${WTHRESOLD}*1000;

HUMAN=" (connected page load: ${TIMECONNECTED}ms, shop page load: ${TIMELOADSHOP}ms, first page:${TIMEFIRST}ms, form post: ${TIMELOGIN}ms user feeling:${TIMEUSER}ms) ";

#'label'=value[UOM];[warn];[crit];[min];[max]
PERFPARSE="page_load=${TIMECONNECTED}ms;${WTHRESOLDMS}ms;${CTHRESOLDMS}ms;${TIMECONNECTED}ms;${TIMECONNECTED}ms;shop_page_load=${TIMELOADSHOP}ms;${WTHRESOLDMS}ms;${CTHRESOLDMS}ms;${TIMELOADSHOP}ms;${TIMELOADSHOP}ms;;;;;first_page=${TIMEFIRST}ms;;;;;form_post=${TIMELOGIN}ms;;;;;user_time_feeling=${TIMEUSER}ms;;;;;";

### CRIT checks ##################

# ensure redirect after login post was a connected success
SUCCESS=`${GREP} "user-menu-toggle" ${BODY}|${GREP} -i "${USERNAME}"`
if [ ! "$?" == "0" ]; then
    echo "$NICK CRITICAL - Failed to get nickname \"${USERNAME}\" in resulting home page. Seems the login failed."${HUMAN}"|"${PERFPARSE};
    exit $CRITICAL;
fi
# ensure shop visit was a success
SUCCESS=`${GREP} "<h1 class=\"site-name element-invisible\">" ${BODYSHOP}| ${GREP} -i "outique"`
if [ ! "$?" == "0" ]; then
    echo "$NICK CRITICAL - Boutique url does not return 'boutique' in hidden branding site name. Seems the login failed on shop site."${HUMAN}"|"${PERFPARSE};
    exit $CRITICAL;
fi
# Check time
if [ ${TIMECONNECTED} -gt ${CTHRESOLDMS} ]; then
    echo "$NICK CRITICAL - Connected page is too long to load! "${HUMAN}"|"${PERFPARSE};
    exit $CRITICAL;
fi
if [ ${TIMELOADSHOP} -gt ${CTHRESOLDMS} ]; then
    echo "$NICK CRITICAL - Shop Connected page is too long to load! "${HUMAN}"|"${PERFPARSE};
    exit $CRITICAL;
fi

### WARN checks ##################

# ensure shop visit was a success
SUCCESS=`${GREP} "user-menu-toggle" ${BODYSHOP}|${GREP} "${USERNAME}"`
if [ ! "$?" == "0" ]; then
    echo "$NICK WARNING - Failed to get nickname \"${USERNAME}\" in resulting shop home page. Seems the login failed on shop site."${HUMAN}"|"${PERFPARSE};
    exit $WARNING;
fi
# Check time
if [ ${TIMECONNECTED} -gt ${WTHRESOLDMS} ]; then
    echo "$NICK WARNING - Connected page is too long to load! "${HUMAN}"|"${PERFPARSE};
    exit $WARNING;
fi
if [ ${TIMELOADSHOP} -gt ${WTHRESOLDMS} ]; then
    echo "$NICK WARNING - Shop Connected page is too long to load! "${HUMAN}"|"${PERFPARSE};
    exit $WARNING;
fi
# ensure logout command was ok for portal -> anonymous page
FAILURE=`${GREP} "user-menu-toggle" ${BODYFAILURE}`
if [ "$?" == "0" ]; then
    echo "$NICK WARNING - Failed to logout from portal site. user-menu-toggle still on resulting page."${HUMAN}"|"${PERFPARSE};
    exit $WARNING;
fi
# ensure logout command was ok for shop -> redirected to portal page
FAILURE=`${GREP} "<h1 class=\"site-name element-invisible\">" ${BODYSHOPFAILURE}| ${GREP} -i "boutique"`
if [ "$?" == "0" ]; then
    echo "$NICK WARNING - Boutique url does is still returning 'boutique' in hidden branding site name. Seems the logout failed on shop site."${HUMAN}"|"${PERFPARSE};
    exit $WARNING;
fi
### OK result ####################

echo "$NICK OK - "${HUMAN}"|"${PERFPARSE};
exit $OK;

