#! /bin/bash

JAMBOXTMP=$PWD/tmp
JAMBOXCPDPORT=9000
JAMBOXWWWPORT=8000

case "$1" in
    start)
        mkdir -p $JAMBOXTMP

        export PYTHONPATH=$PWD

        python jambox.py > $JAMBOXTMP/jambox.log 2>&1 & echo $! > $JAMBOXTMP/jambox.pid
        python www/jamboxwww.py port=$JAMBOXWWWPORT > $JAMBOXTMP/jamboxwww.log 2>&1 & echo $! > $JAMBOXTMP/jamboxwww.pid
    ;;
    stop)
        kill -15 `cat $JAMBOXTMP/jambox.pid`
        #kill -15 `cat $JAMBOXTMP/jamboxwww.pid`
        curl http://127.0.0.1:$JAMBOXWWWPORT/shutdown/
    ;;
esac
