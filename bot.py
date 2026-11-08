#!/usr/bin/env python3
"""
free-node-bot v4
15 subs -> 4 output:
  sub_a.yaml  — http+socks5 (Clash)
  sub_b.yaml  — ss/vmess/vless/trojan/hy2 (Clash)
  sub_a.txt   — http+socks5 (裸URL)
  sub_b.txt   — ss/vmess/vless/trojan/hy2 (裸URL)
"""
import yaml, socket, json, base64, re, time
import urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor
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

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404: return b""
        raise

def parse_yaml(raw):
    if raw[:3] == b"\xef\xbb\xbf": raw = raw[3:]
    d = yaml.safe_load(raw.decode("utf-8", errors="ignore"))
    return d.get("proxies", [])

def parse_b64(raw):
    try:
        txt = base64.b64decode(raw).decode("latin-1")
    except Exception:
        return parse_yaml(raw)
    out = []
    for line in txt.replace("\r", "").split("\n"):
        line = line.strip()
        if not line.startswith(("ss://", "vmess://", "vless://", "trojan://")): continue
        t = line.split(":")[0]
        rest = line[len(t) + 1:]
        try:
            if t == "ss":
                m = re.match(r"^([^@]+)@([\w.-]+):(\d+)", rest)
                if not m: continue
                out.append({"type": "ss", "name": line, "server": m.group(2),
                            "port": int(m.group(3)), "password": urllib.parse.unquote(m.group(1))})
            elif t == "vmess":
                j = json.loads(base64.urlsafe_b64decode(
                    rest + "=" * (-len(rest) % 4)).decode("utf-8", errors="ignore"))
                out.append({"type": "vmess", "name": j.get("ps", line),
                            "server": j["add"], "port": int(j["port"]),
                            "uuid": j["id"], "aid": j.get("aid", 0)})
            elif t in ("vless", "trojan"):
                m = re.match(r"^([^@]+)@([\w.-]+):(\d+)", rest)
                if not m: continue
                out.append({"type": t, "name": line, "server": m.group(2),
                            "port": int(m.group(3)), "uuid": m.group(1)})
        except Exception:
            pass
    return out

def handshake(p):
    srv = str(p.get("server", ""))
    port = int(p.get("port", 443))
    t = p.get("type", "")
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((srv, port))
        if t == "ss":
            s.sendall(bytes([0]) * 16)
            r = s.recv(64)
            ok = len(r) == 64
        elif t in ("vmess", "vless", "ssr", "anytls"):
            s.sendall(bytes([1]))
            r = s.recv(1)
            ok = r == bytes([1])
        elif t in ("hysteria", "hysteria2"):
            s.sendall(bytes([1]))
            r = s.recv(1)
            ok = r == bytes([1])
        elif t == "trojan":
            s.sendall(bytes([1]) + bytes([0]) * 16)
            r = s.recv(1)
            ok = r in (bytes([1]), bytes([0]))
        elif t == "http":
            s.sendall(b"GET / HTTP/1.1\r\nHost: " + srv.encode() + b"\r\n\r\n")
            r = s.recv(4096)
            ok = b"HTTP/1." in r[:100]
        elif t == "socks5":
            s.sendall(bytes([5, 1, 0]))
            r = s.recv(2)
            ok = r == bytes([5, 0])
        else:
            s.sendall(bytes([0]))
            r = s.recv(32)
            ok = len(r) > 0
        s.close()
        return "ALIVE" if ok else "DEAD"
    except Exception:
        return "DEAD"

def speed(p):
    srv = str(p.get("server", ""))
    port = int(p.get("port", 443))
    t = p.get("type", "")
    try:
        s = socket.socket()
        s.settimeout(15)
        s.connect((srv, port))
        if t == "ss":
            s.sendall(bytes([0]) * 16)
            s.recv(64)
        elif t in ("vmess", "vless", "ssr", "anytls"):
            s.sendall(bytes([1]))
            s.recv(1)
        elif t in ("hysteria", "hysteria2"):
            s.sendall(bytes([1]))
            s.recv(1)
        elif t == "trojan":
            s.sendall(bytes([1]) + bytes([0]) * 16)
            s.recv(1)
        elif t == "http":
            pass
        elif t == "socks5":
            s.sendall(bytes([5, 1, 0]))
            s.recv(2)
            s.sendall(bytes([5, 1, 0]))
            s.recv(2)
            s.sendall(bytes([5, 1]) + bytes([0]) * 10)
            r = s.recv(10)
            if r[1] != 0: return -1
        t0 = time.time()
        s.sendall(b"GET /generate_100k HTTP/1.0\r\nHost: cp.cloudflare.com\r\n\r\n")
        buf = b""
        while len(buf) < 102400:
            chunk = s.recv(16384)
            if not chunk: break
            buf += chunk
        s.close()
        return int((time.time() - t0) * 1000)
    except Exception:
        return -1

def to_url(p):
    t = p.get("type", "")
    srv = str(p["server"])
    port = int(p["port"])
    pwd = str(p.get("password", ""))
    uid = str(p.get("uuid", ""))
    if t == "ss":
        return "ss://%s@%s:%d" % (urllib.parse.quote(pwd, safe=""), srv, port)
    if t == "vmess":
        j = {"v": 2, "ps": str(p.get("name", ""))[:200], "add": srv,
              "port": port, "id": uid, "aid": p.get("aid", 0),
              "scy": "auto", "net": "tcp", "type": "tcp"}
        return "vmless://" + base64.urlsafe_b64encode(json.dumps(j).encode()).decode()
    if t == "vless":
        q = []
        if p.get("fingerprint"): q.append("fp=" + str(p["fingerprint"]))
        if p.get("tls"): q.append("security=tls")
        q.append("encryption=" + str(p.get("encryption", "none")))
        return "vless://%s@%s:%d?%s" % (uid, srv, port, "&".join(q))
    if t == "trojan":
        return "trojan://%s@%s:%d" % (uid, srv, port)
    if t in ("hysteria", "hysteria2", "ssr"):
        return "%s://%s@%s:%d" % (t, pwd, srv, port)
    if t == "http":
        return "http://%s@%s:%d" % (urllib.parse.quote(pwd, safe=""), srv, port)
    if t == "socks5":
        return "socks5://%s@%s:%d" % (urllib.parse.quote(pwd, safe=""), srv, port)
    return None

def to_clash(p):
    t = p.get("type", "")
    name = str(p.get("name", str(p.get("server", "?"))))[:60]
    entry = {"name": name, "server": p["server"], "port": int(p["port"])}
    if t == "ss":
        entry.update(type="ss", cipher="aes-256-gcm", password=p.get("password", ""))
    elif t == "vmess":
        entry.update(type="vmess", uuid=p.get("uuid", ""), alterId=p.get("aid", 0), security="auto")
    elif t == "vless":
        entry.update(type="vless", uuid=p.get("uuid", ""),
                     security="tls" if p.get("tls") else "none",
                     encryption=p.get("encryption", "none"))
        if p.get("fingerprint"): entry["fingerprint"] = p["fingerprint"]
    elif t == "trojan":
        entry.update(type="trojan", password=p.get("uuid", ""))
    elif t in ("hysteria", "hysteria2", "ssr"):
        entry.update(type=t, password=p.get("password", ""))
    elif t == "http":
        entry.update(type="http", username="", password=p.get("password", ""))
    elif t == "socks5":
        entry.update(type="socks", username="", password=p.get("password", ""))
    else:
        return None
    return entry

def make_clash_yaml(ps):
    proxies = []
    for p in ps:
        e = to_clash(p)
        if e: proxies.append(e)
    names = [p["name"] for p in proxies]
    return {
        "proxies": proxies,
        "proxy-groups": [
            {"name": "auto", "type": "url-test", "servers": names,
             "url": "http://cp.cloudflare.com/generate_100k",
             "interval": 300, "tolerance": 50},
            {"name": "manual", "type": "select", "servers": ["auto"] + names},
        ],
        "rules": [
            {"type": "ip-cidr", "payload": "127.0.0.0/8", "proxy": "DIRECT"},
            {"type": "ip-cidr", "payload": "10.0.0.0/8", "proxy": "DIRECT"},
            {"type": "ip-cidr", "payload": "172.16.0.0/12", "proxy": "DIRECT"},
            {"type": "ip-cidr", "payload": "192.168.0.0/16", "proxy": "DIRECT"},
            {"type": "domain", "payload": "*.google.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.googleapis.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.gstatic.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.cloudflare.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.cloudflarestorage.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.github.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.githubassets.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.githubusercontent.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.openai.com", "proxy": "auto"},
            {"type": "domain", "payload": "chatgpt.com", "proxy": "auto"},
            {"type": "domain", "payload": "claude.ai", "proxy": "auto"},
            {"type": "domain", "payload": "*.anthropic.com", "proxy": "auto"},
            {"type": "domain", "payload": "cdn.jsdelivr.net", "proxy": "auto"},
            {"type": "domain", "payload": "*.jsdelivr.net", "proxy": "auto"},
            {"type": "domain", "payload": "*.jsdelivr.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.unpkg.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.npmjs.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.npmjs.org", "proxy": "auto"},
            {"type": "domain", "payload": "*.netlify.app", "proxy": "auto"},
            {"type": "domain", "payload": "*.vercel-dns.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.s3.amazonaws.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.cloudfront.net", "proxy": "auto"},
            {"type": "domain", "payload": "*.akamaized.net", "proxy": "auto"},
            {"type": "domain", "payload": "*.azureedge.net", "proxy": "auto"},
            {"type": "domain", "payload": "*.baidu.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.bdimg.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.qq.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.qcloud.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.gtimg.cn", "proxy": "auto"},
            {"type": "domain", "payload": "*.taobao.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.jd.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.weibo.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.sina.com.cn", "proxy": "auto"},
            {"type": "domain", "payload": "*.163.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.126.com", "proxy": "auto"},
            {"type": "domain", "payload": "*.ctrip.com", "proxy": "auto"},
            {"type": "match", "payload": "", "proxy": "auto"},
        ],
    }

def main():
    all_ps = []
    for url in SUBS:
        raw = fetch(url)
        if not raw: continue
        if raw[0:3] == b"\xef\xbb\xbf" or b"---" in raw[:200] or b": " in raw[:100]:
            ps = parse_yaml(raw)
        else:
            ps = parse_b64(raw)
        all_ps.extend(ps)

    seen, uniq = set(), []
    for p in all_ps:
        k = (str(p.get("server", "")), str(p.get("port", "")))
        if k not in seen:
            seen.add(k)
            uniq.append(p)

    with ThreadPoolExecutor(max_workers=30) as ex:
        res = list(ex.map(handshake, uniq))
    alive = [p for p, r in zip(uniq, res) if r == "ALIVE"]

    with ThreadPoolExecutor(max_workers=20) as ex:
        delays = list(ex.map(speed, alive))

    A = [p for p in alive if p.get("type") in ("http", "socks5")]
    B = [p for p in alive if p.get("type") not in ("http", "socks5")]

    idsA = {id(p) for p in A}
    idsB = {id(p) for p in B}
    delA = [d for p, d in zip(alive, delays) if id(p) in idsA]
    delB = [d for p, d in zip(alive, delays) if id(p) in idsB]

    def dump_txt(fn, ps, dlist, label):
        with open(fn, "w") as f:
            f.write("# %s\n# %s\n# %d/%d alive\n\n" % (label, time.strftime("%Y-%m-%d %H:%M"), len(ps), len(uniq)))
            for p, ms in zip(ps, dlist):
                u = to_url(p)
                if u: f.write(u + "\n")

    def dump_clash(fn, ps):
        data = make_clash_yaml(ps)
        with open(fn, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    dump_txt("sub_a.txt", A, delA, "A: http+socks5")
    dump_txt("sub_b.txt", B, delB, "B: ss/vmess/vless/trojan/hy2")
    dump_clash("sub_a.yaml", A)
    dump_clash("sub_b.yaml", B)

    ca = Counter(p.get("type", "") for p in A)
    cb = Counter(p.get("type", "") for p in B)
    with open("summary.txt", "w") as f:
        f.write("# free-node-bot v4\n# %s\n" % time.strftime("%Y-%m-%d %H:%M"))
        f.write("# fetched: %d  dedup: %d  alive: %d\n\n" % (len(all_ps), len(uniq), len(alive)))
        for i, (p, ms) in enumerate(zip(alive, delays)):
            mark = "\u2713" if ms > 0 else "\u2717"
            ms_s = "%dms" % ms if ms > 0 else "--"
            f.write("%s %s  [%s]  %s:%s  %s\n" % (
                mark, str(p.get("name", "?"))[:50],
                p.get("type", ""),
                p.get("server", ""), p.get("port", ""), ms_s))

    print("15 subs")
    print("  fetched: %d" % len(all_ps))
    print("  dedup:   %d" % len(uniq))
    print("  ALIVE:   %d" % len(alive))
    print("\n  A: %d" % len(A))
    for t, c in ca.most_common(): print("    %s: %d" % (t, c))
    print("\n  B: %d" % len(B))
    for t, c in cb.most_common(): print("    %s: %d" % (t, c))

if __name__ == "__main__":
    main()
