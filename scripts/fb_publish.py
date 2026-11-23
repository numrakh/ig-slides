#!/usr/bin/env python3
"""Publish a carousel (multi-photo post) to the Facebook Page via the Graph API.
Usage: python3 -I fb_publish.py caption.txt URL1 URL2 ... (1-10 public HTTPS JPEG URLs)
       python3 -I fb_publish.py --check   (verify token, print Page name and id)
       python3 -I fb_publish.py --dry-run caption.txt URL1 ...  (upload unpublished photos, do not post)
Reads FACEBOOK_PAGE_TOKEN from env (a system user token; strips <> and whitespace).
The Page token is fetched at runtime from /me/accounts. Never prints a token.
Optional FACEBOOK_PAGE_ID picks the Page when the token has several.
Prints JSON {"id":..., "permalink_url":...} on success.
"""
import json, os, re, sys, urllib.parse, urllib.request

G = "https://graph.facebook.com/v21.0"
TOKEN = re.sub(r"[<>\s\"']", "", os.environ.get("FACEBOOK_PAGE_TOKEN", ""))
if not TOKEN:
    sys.exit("FACEBOOK_PAGE_TOKEN missing")


def call(method, path, token, **params):
    params["access_token"] = token
    data = urllib.parse.urlencode(params)
    url = f"{G}/{path}"
    req = urllib.request.Request(url + ("?" + data if method == "GET" else ""),
                                 data=data.encode() if method == "POST" else None, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        out = json.loads(e.read() or b"{}")
    if "error" in out:
        raise SystemExit(f"API error on {path}: {out['error'].get('message')}")
    return out


pages = call("GET", "me/accounts", TOKEN, fields="id,name,access_token,tasks")["data"]
want = os.environ.get("FACEBOOK_PAGE_ID", "").strip()
pages = [p for p in pages if not want or p["id"] == want]
if not pages:
    sys.exit("no Facebook Page available for this token")
page = pages[0]
pid, ptok = page["id"], page["access_token"]

args = sys.argv[1:]
if args == ["--check"]:
    if "CREATE_CONTENT" not in page.get("tasks", []):
        sys.exit(f"token cannot post to Page {page['name']}")
    print(json.dumps({"page": page["name"], "id": pid}))
    sys.exit()

dry = args[:1] == ["--dry-run"]
if dry:
    args = args[1:]
caption = open(args[0], encoding="utf-8").read().strip()
urls = args[1:]
if not 1 <= len(urls) <= 10:
    sys.exit("need 1-10 image URLs")
photos = [call("POST", f"{pid}/photos", ptok, url=u, published="false")["id"] for u in urls]
if dry:
    for ph in photos:
        call("DELETE", ph, ptok)
    print(json.dumps({"dry_run": "ok", "items": len(photos), "page": page["name"]}))
    sys.exit()
params = {f"attached_media[{i}]": json.dumps({"media_fbid": ph}) for i, ph in enumerate(photos)}
post = call("POST", f"{pid}/feed", ptok, message=caption, **params)
info = call("GET", post["id"], ptok, fields="id,permalink_url,created_time")
print(json.dumps(info))
