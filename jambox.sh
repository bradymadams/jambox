#! /bin/bash

JAMBOXTMP=$PWD/tmp
JAMBOXCPDPORT=9000
JAMBOXWWWPORT=8000

case "$1" in
    start)
        mkdir -p $JAMBOXTMP

        export PYTHONPATH=$PWD

        python controlpaneld.py > $JAMBOXTMP/controlpaneld.log 2>&1 & echo $! > $JAMBOXTMP/controlpaneld.pid
        python controlpanelm.py > $JAMBOXTMP/controlpanelm.log 2>&1 & echo $! > $JAMBOXTMP/controlpanelm.pid
        python www/jamboxwww.py port=$JAMBOXWWWPORT > $JAMBOXTMP/jamboxwww.log 2>&1 & echo $! > $JAMBOXTMP/jamboxwww.pid
    ;;
    stop)
        kill -15 `cat $JAMBOXTMP/controlpaneld.pid`
        kill -15 `cat $JAMBOXTMP/controlpanelm.pid`
        #kill -15 `cat $JAMBOXTMP/jamboxwww.pid`
        curl http://127.0.0.1:$JAMBOXWWWPORT/shutdown/
    ;;
esac
