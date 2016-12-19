#!/bin/bash

SLACKPROCESS="/usr/bin/sudo -u slacky /opt/slackbot/slackbot/version2/main.py"
SLACKPROCESS_CHECK="/opt/slackbot/slackbot/version2/main.py"
TIMEOUT=10

while :
do
	ps_out=`ps -ef | grep $SLACKPROCESS_CHECK | grep -v 'grep' ` 
	result=$(echo $ps_out)
	date=`date`

	if [[ "$result" != "" ]]; then
  		continue	
	else
		echo "$date Slack not running, restarting."
  		$($SLACKPROCESS)
	fi
	sleep $TIMEOUT 
done
