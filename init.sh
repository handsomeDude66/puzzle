if [ -f .venv ]; then
    rm -r .venv
fi

python -m venv .venv

source .venv/bin/activate

pip install -r proxy_pool/requirements.txt
