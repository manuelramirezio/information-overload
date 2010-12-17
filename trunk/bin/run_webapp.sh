#!/bin/bash

##################################################################
#    Copyright 2008 Spike^ekipS <spikeekips@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##################################################################

[ -z $1 ] && exit 1;

port=8000
if [ ! -z $2 ];then
    port=$2
fi

reactor="epoll"
if [ ! -z $3 ];then
    reactor=$3
fi

_ff=`dirname $0`; _ff=`(cd $_ff; pwd)`
ff=$_ff/`basename $0`

_cur=`dirname $0`/../
root=`(cd $_cur; pwd)`

source $root/bin/env

pid=/tmp/I.O-$port.pid

case $1 in
	start)
        cd $root/apps/webapp

        export DJANGO_SETTINGS_MODULE="master.settings"

		python `which twistd` -r $reactor -y $root/library/python/server.py --pidfile=$pid --prefix=$port
	;;
	stand)
        cd $root/apps/webapp

        export DJANGO_SETTINGS_MODULE="master.settings"

		python `which twistd` -r $reactor -ny $root/library/python/server.py --pidfile=$pid --prefix=$port
	;;
	stop)
        if [ ! -f $pid ];then
            echo "Failed to stop. No such pid file, "
            exit 1
        fi

		kill -9 `cat $pid` &>/dev/null
        if [ $? == "0" ];then
            echo "Successfully stopped."
        else
            echo "Failed to stop."
        fi
	;;
	restand)
		bash $0 stop
		sleep 1
		bash $0 stand $2
	;;
	restart)
		bash $0 stop
		sleep 1
		bash $0 start $2
	;;
esac


