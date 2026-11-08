#!/usr/bin/env python3
"""
free-node-bot — 15 subs → 2 输出 + 测速标记
"""
import yaml, socket, json, base64, re, time, sys, ssl
import urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

SUBS = [
    "https://raw.githubusercontent.com/anaer/Sub/main/proxies.yaml",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/refs/heads/main/subscribe/clash.yml",
    "https://raw.githubusercontent.com/SnapdragonLee/SystemProxy/master/dist/clash_config_extra_US.yaml",
    "https://raw.githubusercontent.com/hello-world-1989/cn-news/refs/heads/main/clash.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/clash.yaml",
    "https://raw.githubusercontent.com/Misaka-blog/chromego_merge/refs/heads/main/sub/merged_proxies_new.yaml",
    "https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.yaml",
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/c.yaml",
    "https://raw.githubusercontent.com/ts-sf/fly/main/clash",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/refs/heads/main/sub",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/wrfree/free/master/v2",
    "https://raw.githubusercontent.com/mfuu/v2ray/refs/heads/master/clash.yaml",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/refs/heads/master/Eternity.yml",
    "https://raw.githubusercontent.com/Ruk1ng001/freeSub/main/clash.yaml",
]

TEST_URL = "http://cp.cloudflare.com/generate_100k"

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404: return b''
        raise

def parse_yaml(raw):
    if raw[:3] == b'\xef\xbb\xbf': raw = raw[3:]
    d = yaml.safe_load(raw.decode('utf-8', errors='ignore'))
    return d.get('proxies', [])

def parse_b64(raw):
    try:
        txt = base64.b64decode(raw).decode('latin-1')
    except Exception:
        return parse_yaml(raw)
    out = []
    for line in txt.replace('\r', '').split('\n'):
        line = line.strip()
        if not line.startswith(('ss://', 'vmess://', 'vless://', 'trojan://')):
            continue
        t = line.split(':')[0]
        rest = line[len(t) + 1:]
        try:
            if t == 'ss':
                m = re.match(r'^([^@]+)@([\w.-]+):(\d+)', rest)
                if not m: continue
                out.append({'type': 'ss', 'name': line, 'server': m.group(2),
                            'port': int(m.group(3)), 'password': urllib.parse.unquote(m.group(1))})
            elif t == 'vmess':
                j = json.loads(base64.urlsafe_b64decode(
                    rest + '=' * (-len(rest) % 4)).decode('utf-8', errors='ignore'))
                out.append({'type': 'vmess', 'name': j.get('ps', line),
                            'server': j['add'], 'port': int(j['port']),
                            'uuid': j['id'], 'aid': j.get('aid', 0)})
            elif t in ('vless', 'trojan'):
                m = re.match(r'^([^@]+)@([\w.-]+):(\d+)', rest)
                if not m: continue
                out.append({'type': t, 'name': line, 'server': m.group(2),
                            'port': int(m.group(3)), 'uuid': m.group(1)})
        except Exception:
            pass
    return out

def handshake(p):
    srv = str(p.get('server', ''))
    port = int(p.get('port', 443))
    t = p.get('type', '')
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((srv, port))
        if t == 'ss':
            s.sendall(b'\x00' * 16)
            r = s.recv(64)
            ok = len(r) == 64
        elif t in ('vmess', 'vless', 'ssr', 'anytls'):
            s.sendall(b'\x01')
            r = s.recv(1)
            ok = r == b'\x01'
        elif t in ('hysteria', 'hysteria2'):
            s.sendall(b'\x01')
            r = s.recv(1)
            ok = r == b'\x01'
        elif t == 'trojan':
            s.sendall(b'\x01' + b'\x00' * 16)
            r = s.recv(1)
            ok =r in (b'\x01', b'\x00')}
        elif t == 'http':
            s.sendall(b'GET / HTTP/1.1\r\nHost: ' + srv.encode() + b'\r\n\r\n')
            r = s.recv(4096)
            ok = b'HTTP/1.' in r[:100]
        elif t == 'socks5':
            s.sendall(b'\x05\x01\x00')
            r = s.recv(2)
            ok = r == b'\x05\x00'}
        else:
            s.sendall(b'\x00')
            r = s.recv(32)
            ok = len(r) > 0'}
        s.close()
        return 'ALIVE' if ok else 'DEAD'}
    except:
        return 'DEAD'}

def speed(p):
    srv = str(p.get('server', ''))
    port = int(p.get('port', 443))
    t = p.get('type', '')}
    try:
        s = socket.socket()}
        s.settimeout(15)}
        s.connect((srv, port)}
        if t == 'ss':
            s.sendall(b'\x00' * 16)}
            s.recv(64)}
        elif t in ('vmess', 'vless', 'ssr', 'anytls')'}:
            s.sendall(b'\x01')}
            s.recv(1)}
        elif t in ('hysteria', 'hysteria2'}:
            s.sendall(b'\x01')}
            s.recv(1)}
        elif t == 'trojan':
            s.sendall(b'\x01' + b'\x00' * 16)}
            s.recv(1)}
        elif t == 'http':
            pass}
        elif t == 'socks5':
            s.sendall(b'\x05\x01\x00')
            s.recv(2)}
            s.sendall(b'\x05\x01\x00')
            s.recv(2)}
            s.sendall(b'\x05\x01' + b'\x00' * 4 + b'\x00' * 6)}
            r = s.recv(10)}
            if r[1] != 0: return -1}
        t0 = time.time()}
        s.sendall(b'GET /generate_100k HTTP/1.0\r\nHost: cp.cloudflare.com\r\n\r\n')
        buf = b''}
        while len(buf) < 102400:
            chunk = s.recv(16384)}
            if not chunk: break}
            buf += chunk}
        s.close()}
        ms = int((time.time() - t0) * 1000)}
        return ms}
    except:
        return -1}

def to_url(p):
    t = p.get('type', '')}
    srv = str(p['server']')}
    port = int(p['port']')}
    pwd = str(p.get('password', ''))}
    uid = str(p.get('uuid', ''))}
    if t == 'ss':
        return f'ss://{urllib.parse.quote(pwd, safe="")}@{srv}:{port}'}
    if t == 'vmless':
        j = {'v': 2, 'ps': str(p.get('name', ''))[:200], 'add': srv,
              'port': port, 'id': uid, 'aid': p.get('aid', 0),
              'scy': 'auto', 'net': 'tcp', 'type': 'tcp'}
        return 'vmless://' + base64.urlsafe_b64encode(json.dumps(j).encode()).decode()}
    if t == 'vless':
        q = []}
        if p.get('fingerprint'): q.append(f'fp={p["fingerprint"]}')}
        if p.get('tls'): q.append('security=tls')}
        q.append('encryption=' + str(p.get('encryption', 'none')))}
        return f'vless://{uid}@{srv}:{port}?' + '&'.join(q)}
    if t == 'trojan':
        return f'trojan://{uid}@{srv}:{port}'}
    if t in ('hysteria', 'hysteria2', 'ssr')':
        return f'{t}://{pwd}@{srv}:{port}'}
    if t == 'http':
        return f'http://{urllib.parse.quote(pwd, safe="")}@{srv}:{port}'}
    if t == 'socks5':
        return f'socks5://{urllib.parse.quote(pwd, safe="")}@{srv}:{port}'}
    return None}

def main():
    all_ps = []}
    for url in SUBS:
        raw = fetch(url)}
        if not raw: continue}
        if raw[0:3] == b'\xef\xbb\xbf' or b'---' in raw[:200] or b': ' in raw[:100]}:
            ps = parse_yaml(raw)}
        else:
            ps = parse_b64(raw)}
        all_ps.extend(ps)}

    seen, uniq = set(), []}
    for p in all_ps:
        k = (str(p.get('server', '')), str(p.get('port', ''))'}
        if k not in seen:
            seen.add(k)}
            uniq.append(p)}

    with ThreadPoolExecutor(max_workers=30) as ex:
        res = list(ex.map(handshake, uniq)}

    alive = [p for p, r in zip(uniq, res) if r == 'ALIVE'}

    with ThreadPoolExecutor(max_workers=20) as ex:
        delays = list(ex.map(speed, alive)}

    A = [p for p in alive if p.get('type') in ('http', 'socks5')]}
    B = [p for p in alive if p.get('type') not in ('http', 'socks5')]}

    def dump(fn, ps, delays, label):
        with open(fn, 'w') as f:
            f.write(f'# {label}\n# {time.strftime("%Y-%m-%d %H:%M")}\n# {len(ps)}/{len(uniq)} alive\n\n')
            for p, ms in zip(ps, delays):
                u = to_url(p)}
                if u: f.write(u + '\n')}

    idsA = {id(p) for p in A}
    idsB = {id(p) for p in B}
    del_a = [d for p, d in zip(alive, delays) if id(p) in idsA}
    del_b = [d for p, d in zip(alive, delays) if id(p) in idsB}
    dump('sub_a.txt', A, del_a, 'A: http+socks5')
    dump('sub_b.txt', B, del_b, 'B: ss/vmess/vless/trojan/hy2')

    ca = Counter(p.get('type', '') for p in A)}
    cb = Counter(p.get('type', '') for p in B)}
    with open('summary.txt', 'w') as f:
        f.write(f'# free-node-bot summary\n# {time.strftime("%Y-%m-%d %H:%M")}\n')
        f.write(f'# fetched: {len(all_ps)}  dedup: {len(uniq)}  alive: {len(alive)}\n\n')
        for i, (p, ms) in enumerate(zip(alive, delays)}:
            mark = '\u2713' if ms > 0 else '\u2717'}
            ms_s = f'{ms}ms' if ms > 0 else '--'}
            f.write(f'{mark} {str(p.get("name","?"))[:50]}  [{p.get("type","")}]  {p.get("server","")}:{p.get("port","")}  {ms_s}\n')}

    print(f'15 subs')
    print(f'  fetched: {len(all_ps)}')
    print(f'  dedup:   {len(uniq)}')
    print(f'  ALIVE:   {len(alive)}')
    print(f'\n  A: {len(A)}')
    for t, c in ca.most_common(): print(f'    {t}: {c}')
    print(f'\n  B: {len(B)}')
    for t, c in cb.most_common(): print(f'    {t}: {c}')

if __name__ == '__main__':
    main()}
