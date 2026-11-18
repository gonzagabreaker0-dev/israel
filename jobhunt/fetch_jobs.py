#!/usr/bin/env python3
"""Fetch recent OnlineJobs.ph listings that match the profile's search terms.

  python3 jobhunt/fetch_jobs.py [--days 2] [--out jobhunt/out/jobs.json]

Reads only public job pages (no login, nothing is submitted). Writes a JSON list of
jobs with title, pay, type, hours, date, skills, full description and a link.
"""
import argparse, datetime as dt, html, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.onlinejobs.ph"
UA = {"User-Agent": "Mozilla/5.0 (job-digest; personal use)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def text(fragment):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", fragment, flags=re.S)
    t = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", t)).strip()


def search(keyword, pages=2):
    links = []
    for p in range(pages):
        q = urllib.parse.urlencode({"jobkeyword": keyword}) + (f"&page={p * 30}" if p else "")
        try:
            h = get(f"{BASE}/jobseekers/jobsearch?{q}")
        except Exception as e:  # network hiccup: skip this page
            print("search failed", keyword, e, file=sys.stderr); break
        found = re.findall(r'href="(/jobseekers/job/[^"#?]+)"', h)
        new = [l for l in dict.fromkeys(found) if l not in links]
        if not new: break
        links += new
        time.sleep(1)
    return links


def field(t, name, nxt):
    m = re.search(rf"{name}\s*\n(.*?)\n\s*(?:{nxt})", t, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def job(link):
    h = get(BASE + link)
    t = text(h)
    title = html.unescape(re.search(r"<title>(.*?)\s*-\s*OnlineJobs\.ph</title>", h, re.S).group(1)).strip()
    title = html.unescape(re.sub(r"\s+\d+$", "", title))
    overview = field(t, "JOB OVERVIEW", "SKILL REQUIREMENT")
    skills = field(t, "SKILL REQUIREMENT", "Contact Person|ABOUT|Similar|Apply|$")
    return {
        "id": re.search(r"(\d+)$", link).group(1), "title": title, "url": BASE + link,
        "type": field(t, "TYPE OF WORK", "WAGE"), "pay": field(t, "WAGE / SALARY", "HOURS"),
        "hours": field(t, "HOURS PER WEEK", "DATE"), "date": field(t, "DATE UPDATED", "JOB OVERVIEW"),
        "skills": [s for s in skills.split("\n") if 2 < len(s) < 60][:15],
        "description": overview[:6000],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=2, help="only jobs updated within this many days")
    ap.add_argument("--profile", default=os.path.join(HERE, "profile.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "out", "jobs.json"))
    ap.add_argument("--max", type=int, default=40)
    a = ap.parse_args()
    prof = json.load(open(a.profile))
    links = []
    for kw in prof["search_terms"]:
        for l in search(kw):
            if l not in links: links.append(l)
    cutoff = dt.date.today() - dt.timedelta(days=a.days)
    exclude = [w.lower() for w in prof.get("exclude_words", [])]
    jobs = []
    for l in links:
        if len(jobs) >= a.max: break
        try:
            j = job(l)
        except Exception as e:
            print("job failed", l, e, file=sys.stderr); continue
        try:
            d = dt.datetime.strptime(j["date"], "%b %d, %Y").date()
            if d < cutoff: continue
        except ValueError:
            pass
        blob = (j["title"] + " " + j["description"]).lower()
        if any(w in blob for w in exclude): continue
        jobs.append(j)
        time.sleep(0.7)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(jobs, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"{len(links)} links, {len(jobs)} recent jobs -> {a.out}")


if __name__ == "__main__":
    main()
