#!/bin/sh


#####################################################
# Nagios plugin to check size of files              #
#####################################################

MINCRIT=0
MINWARN=0
MAXCRIT=99999999999999
MAXWARN=99999999999999
VERBOSE=0
MISSINGOK=0

outputDebug() {
    if [ $VERBOSE -gt 0 ] ; then
        echo $1
    fi
}

if [ $# -eq 0 ] ; then
    TEMP="-h"
else 
    TEMP=`getopt -o vhm -l 'help,verbose,missingok,minwarn:,mincrit:,maxwarn:,maxcrit:' -- "$@"`
fi
outputDebug "Processing Args $TEMP"
if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi
eval set -- "$TEMP"

while true ; do
    case "$1" in
        -v|--verbose) VERBOSE=1 ; outputDebug "Verbose Mode ON" ; shift ;;
        -h|--help) echo "Usage: $0 [--minwarn size] [--maxwarn size] [--mincrit size] [--maxcrit size] [-m|--missingok]  [-v|--verbose] <list of files or directies>" ; exit 0;;
        -m|--missingok) outputDebug "Allow missing files" ; MISSINGOK=1 ; shift ;;
        --minwarn) outputDebug "Option $1 is $2" ; MINWARN=$2 ; shift 2;;
        --maxwarn) outputDebug "Option $1 is $2" ; MAXWARN=$2 ; shift 2;;
        --mincrit) outputDebug "Option $1 is $2" ; MINCRIT=$2 ; shift 2;;
        --maxcrit) outputDebug "Option $1 is $2" ; MAXCRIT=$2 ; shift 2;;
        --) shift ; break ;;
        *) echo "Internal error! - found $1 and $2" ; exit 3 ;;
    esac
done

assertSizeOK() {
    outputDebug "Size of $2 is $1, validating"
    if [ $1 -lt $MINCRIT ] ; then
        echo "FILE Critical: Size of $SIZE < $MINCRIT for $2" ; exit 2
    fi
    if [ $1 -lt $MINWARN ] ; then
        echo "FILE Warning: Size of $SIZE < $MINWARN for $2" ; exit 1
    fi
    if [ $1 -ge $MAXCRIT ] ; then
        echo "FILE Critical: Size of $SIZE > $MAXCRIT for $2" ; exit 2
    fi
    if [ $1 -ge $MAXWARN ] ; then
        echo "FILE Warning: Size of $SIZE > $MAXWARN for $2" ; exit 1
    fi
}

checkDir() {
    SIZE=`du -s $1 | cut -f 1`
    assertSizeOK $SIZE $1
}

checkFile() {
    SIZE=`stat --format %s $1`
    assertSizeOK $SIZE $1
}

#echo "Remaining arguments:"
CNT=0
for arg do 
    outputDebug '--> '"\`$arg'" 
    CNT=$(( $CNT + 1 ))
    if [ -f "$arg" ] ; then
        checkFile "$arg"
    elif [ -d "$arg" ] ; then
        checkDir "$arg"
    else 
        if [ $MISSINGOK -eq 0 ] ; then
                echo "Not a file or directory (or doesn't exist), don't know what to do with $arg"
                exit 3
        else 
                outputDebug "Skipping nonexistent file $arg"
        fi
    fi
done

if [ $MISSINGOK -eq 0 ] && [ $CNT -eq 0 ] ; then
    echo "ERROR, no files supplied or found"
    exit 3
fi

echo "FILE OK: All files ($CNT) fall within requested parameters"
exit 0




