#!/usr/bin/env python3
"""Publish a carousel to Threads via the Threads API.
Usage: python3 -I threads_publish.py caption.txt URL1 URL2 ... (2-20 public HTTPS JPEG URLs)
       python3 -I threads_publish.py --check   (verify token, print username)
       python3 -I threads_publish.py --dry-run caption.txt URL1 ...  (create containers, do not publish)
Reads THREADS_ACCESS_TOKEN from env (strips <> and whitespace). Never prints the token.
Threads allows one topic tag per post and 500 characters of text, so the caption's
hashtags are dropped and the text is trimmed to fit.
Prints JSON {"id":..., "permalink":...} on success.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

G = "https://graph.threads.net/v1.0"
TOKEN = re.sub(r"[<>\s\"']", "", os.environ.get("THREADS_ACCESS_TOKEN", ""))
if not TOKEN:
    sys.exit("THREADS_ACCESS_TOKEN missing")


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params)
    url = f"{G}/{path}"
    req = urllib.request.Request(url + ("?" + data if method == "GET" else ""),
                                 data=data.encode() if method == "POST" else None, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        out = json.loads(e.read() or b"{}")
    out.pop("paging", None)
    if "error" in out:
        raise SystemExit(f"API error on {path}: {out['error'].get('message')}")
    return out


def wait_ready(cid, tries=30):
    for _ in range(tries):
        r = call("GET", cid, fields="status,error_message")
        s = r.get("status")
        if s == "FINISHED":
            return
        if s in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container {cid} status {s}: {r.get('error_message')}")
        time.sleep(4)
    raise SystemExit(f"container {cid} not ready")


def threads_text(caption):
    lines = [l for l in caption.splitlines() if not re.fullmatch(r"\s*(#\S+\s*)+", l)]
    text = re.sub(r"\s#\S+", "", "\n".join(lines)).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text if len(text) <= 500 else text[:497].rstrip() + "..."


def facebook_too(cap_path, urls):
    """Best effort: also post to the Facebook Page via fb_publish.py --after. Never raises."""
    if not os.environ.get("FACEBOOK_PAGE_TOKEN", "").strip():
        return
    import subprocess
    fb = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_publish.py")
    try:
        r = subprocess.run([sys.executable, "-I", fb, "--after", cap_path, *urls],
                           capture_output=True, text=True, timeout=900)
        msg = (r.stdout.strip() or r.stderr.strip())[-300:]
        print(f"facebook: {msg}", file=sys.stderr)
    except Exception as e:
        print(f"facebook: error {e}", file=sys.stderr)


args = sys.argv[1:]
me = call("GET", "me", fields="id,username")
if args == ["--check"]:
    print(json.dumps({"username": me["username"]}))
    sys.exit()

dry = args[:1] == ["--dry-run"]
if dry:
    args = args[1:]
caption = threads_text(open(args[0], encoding="utf-8").read())
urls = args[1:]
if not 2 <= len(urls) <= 20:
    sys.exit("need 2-20 image URLs")
if not dry:
    import atexit
    atexit.register(facebook_too, args[0], urls)
uid = me["id"]
kids = [call("POST", f"{uid}/threads", media_type="IMAGE", image_url=u, is_carousel_item="true")["id"] for u in urls]
for k in kids:
    wait_ready(k)
cid = call("POST", f"{uid}/threads", media_type="CAROUSEL", children=",".join(kids), text=caption)["id"]
wait_ready(cid)
if dry:
    print(json.dumps({"dry_run": "ok", "items": len(kids), "text_chars": len(caption)}))
    sys.exit()
mid = call("POST", f"{uid}/threads_publish", creation_id=cid)["id"]
info = call("GET", mid, fields="id,permalink,timestamp")
print(json.dumps(info))
