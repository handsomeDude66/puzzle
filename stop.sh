if netstat -tunpl | grep :5010 >/dev/null 2>&1; then
    kill $(ps -ef | grep proxyPool.py | grep -v grep | awk '{print $2}')
fi
