#!/bin/bash
# Test: can urlopen reach VCF Installer through SOCKS via PySocks?
python3 -c "
import os, sys
print(f'Python: {sys.executable} ({sys.version.split()[0]})')

import socks, socket
from urllib.parse import urlparse

p = urlparse('socks5h://localhost:1080')
socks.set_default_proxy(socks.SOCKS5, p.hostname, p.port, rdns=True)
socket.socket = socks.socksocket

from urllib.request import Request, urlopen
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print('Connecting to VCF Installer via SOCKS...')
try:
    r = urlopen(Request('https://vcf-installer.lab.dreamfold.dev/'), context=ctx, timeout=30)
    print(f'HTTP {r.status} — connection works')
except Exception as e:
    print(f'FAILED: {e}')
"
