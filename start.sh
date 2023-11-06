./stop.sh

if ! netstat -tunpl | grep :6379 >/dev/null 2>&1; then
    sudo systemctl start redis
fi

source .venv/bin/activate
export DB_CONN="redis://:@127.0.0.1:6379/0"
nohup python proxy_pool/proxyPool.py schedule >/dev/null 2>&1 &
nohup python proxy_pool/proxyPool.py server >/dev/null 2>&1 &
