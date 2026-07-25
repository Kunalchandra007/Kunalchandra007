#!/usr/bin/env python3
"""
Regenerates stats.svg, langs.svg, trophies.svg from live GitHub data.
Same black/green visual design as the hand-built versions — just fed by
real numbers pulled from the GitHub REST API on every run.
"""
import os, sys, json, math
from urllib.request import Request, urlopen
from urllib.error import HTTPError

USERNAME = os.environ.get("GH_USERNAME", "Kunalchandra007")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

purple = "#10b981"; purple2 = "#34d399"; green = "#4ade80"; green2 = "#a3e635"
bg = "#000000"; card_bg = "#061209"; card_border = "#1e4d2b"
text_main = "#e8f5ec"; text_dim = "#7fae8f"

LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#f1e05a",
    "Java": "#b07219", "C++": "#f34b7d", "C": "#555555", "HTML": "#e34c26",
    "CSS": "#563d7c", "PHP": "#4F5D95", "Go": "#00ADD8", "Jupyter Notebook": "#DA5B0B",
    "Shell": "#89e051", "C#": "#178600", "Ruby": "#701516",
}

def api(path):
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USERNAME}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req) as r:
            return json.loads(r.read().decode())
    except HTTPError as e:
        print(f"API error on {path}: {e.code} {e.read().decode()[:300]}", file=sys.stderr)
        sys.exit(1)

def fetch_all_repos():
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos

def rank_letter(score):
    # score 0-100 -> letter, mirrors github-readme-stats style bands
    if score >= 85: return "S"
    if score >= 65: return "A+"
    if score >= 50: return "A"
    if score >= 35: return "B+"
    if score >= 20: return "B"
    if score >= 10: return "C"
    return "D"

def small_rank(n, s_,a_,b_,c_):
    if n >= s_: return "S"
    if n >= a_: return "A"
    if n >= b_: return "B"
    if n >= c_: return "C"
    return "D"

def wrap(w, h, body, rid):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <clipPath id="rc{rid}"><rect x="0" y="0" width="{w}" height="{h}" rx="14"/></clipPath>
    <linearGradient id="bgg{rid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg}"/><stop offset="100%" stop-color="#08150c"/>
    </linearGradient>
  </defs>
  <g clip-path="url(#rc{rid})">
    <rect width="{w}" height="{h}" fill="url(#bgg{rid})"/>
    <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="none" stroke="{purple2}" stroke-width="1" opacity="0.5"/>
    {body}
  </g>
</svg>'''

def build_stats(repos_count, stars, followers):
    W, H = 440, 195
    score = min(100, repos_count*0.8 + stars*1.5 + followers*1.2)
    letter = rank_letter(score)
    ring_pct = min(1.0, score/100)
    circ = 2*3.14159*46
    dash = circ*ring_pct
    ring = f'''
    <g transform="translate(70,97)">
      <circle r="46" fill="none" stroke="{card_border}" stroke-width="9"/>
      <circle r="46" fill="none" stroke="url(#ringGradS)" stroke-width="9" stroke-linecap="round"
        stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ:.1f}" transform="rotate(-90)">
        <animate attributeName="stroke-dashoffset" values="{circ:.1f};{circ-dash:.1f}" dur="1.8s" begin="0.2s" fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1"/>
      </circle>
      <text text-anchor="middle" y="-2" font-family="'Fira Code',monospace" font-size="20" font-weight="800" fill="{text_main}">{letter}</text>
      <text text-anchor="middle" y="16" font-family="'Fira Code',monospace" font-size="9" fill="{text_dim}">RANK</text>
    </g>'''
    stats = [("Total Repositories", str(repos_count), purple2),
             ("Total Stars Earned", str(stars), green2),
             ("Followers", str(followers), purple2)]
    rows = []
    for i,(label,val,col) in enumerate(stats):
        yy = 30 + i*38
        delay = 0.3 + i*0.15
        rows.append(f'''
        <g transform="translate(150,{yy})" opacity="0">
          <animate attributeName="opacity" values="0;0;1" keyTimes="0;{min(delay/2.2,0.9):.3f};1" dur="2.2s" begin="0s" fill="freeze"/>
          <animateTransform attributeName="transform" type="translate" values="180,{yy};180,{yy};150,{yy}" keyTimes="0;{min(delay/2.2,0.9):.3f};1" dur="2.2s" begin="0s" fill="freeze" additive="sum"/>
          <circle cx="0" cy="0" r="3" fill="{col}"/>
          <text x="12" y="4" font-family="'Fira Code',monospace" font-size="12.5" fill="{text_dim}">{label}</text>
          <text x="260" y="4" text-anchor="end" font-family="'Fira Code',monospace" font-size="13" font-weight="700" fill="{col}">{val}</text>
        </g>''')
    body = f'''
    <defs><linearGradient id="ringGradS" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{purple2}"/><stop offset="100%" stop-color="{green2}"/></linearGradient></defs>
    <text x="20" y="26" font-family="'Fira Code',monospace" font-size="13" font-weight="700" fill="{text_main}">Kunal Chandra's GitHub Stats</text>
    {ring}
    {"".join(rows)}
    '''
    return wrap(W, H, body, "stats")

def build_langs(lang_pct):
    W, H = 300, 195
    top = lang_pct[:5]
    lang_rows, bar_segs = [], []
    xoff = 20
    for i,(name,pct) in enumerate(top):
        col = LANG_COLORS.get(name, "#8b949e")
        yy = 60 + i*22
        lang_rows.append(f'''
        <g transform="translate(20,{yy})">
          <text x="0" y="4" font-family="'Fira Code',monospace" font-size="11" fill="{text_main}">{name}</text>
          <text x="260" y="4" text-anchor="end" font-family="'Fira Code',monospace" font-size="10" fill="{text_dim}">{pct*100:.0f}%</text>
        </g>''')
        seg_w = 260*pct
        delay = 0.2+i*0.12
        bar_segs.append(f'''<rect x="{xoff:.1f}" y="36" width="0" height="10" fill="{col}">
          <animate attributeName="width" values="0;0;{seg_w:.1f}" keyTimes="0;{min(delay/1.6,0.85):.3f};1" dur="1.6s" begin="0.1s" fill="freeze"/>
        </rect>''')
        xoff += seg_w
    body = f'''
    <text x="20" y="24" font-family="'Fira Code',monospace" font-size="13" font-weight="700" fill="{text_main}">Most Used Languages</text>
    <rect x="20" y="36" width="260" height="10" rx="5" fill="{card_border}"/>
    <clipPath id="barclip"><rect x="20" y="36" width="260" height="10" rx="5"/></clipPath>
    <g clip-path="url(#barclip)">{"".join(bar_segs)}</g>
    {"".join(lang_rows)}
    '''
    return wrap(W, H, body, "langs")

def build_trophies(repos_count, stars, followers):
    W, H = 850, 180
    r_rank = small_rank(repos_count, 60, 30, 15, 5)
    s_rank = small_rank(stars, 50, 20, 5, 1)
    f_rank = small_rank(followers, 50, 20, 5, 1)
    trophies = [("YOLO","S",purple2), ("Pull Shark","A",green2), ("Quickdraw","B",purple2),
                ("Repositories", r_rank, green2), ("Stars", s_rank, purple2), ("Followers", f_rank, green2)]
    cw = 130
    cells = []
    for i,(name,rank,col) in enumerate(trophies):
        x = 20 + i*(cw+8)
        delay = 0.15*i
        cells.append(f'''
        <g transform="translate({x},20)" opacity="0">
          <animate attributeName="opacity" values="0;0;1" keyTimes="0;{min(delay/2.3,0.85):.3f};1" dur="2.3s" begin="0s" fill="freeze"/>
          <animateTransform attributeName="transform" type="scale" values="0.6;0.6;1" keyTimes="0;{min(delay/2.3,0.85):.3f};1" dur="2.3s" begin="0s" fill="freeze" additive="sum"/>
          <rect width="{cw}" height="140" rx="12" fill="{card_bg}" stroke="{col}" stroke-width="1.3"/>
          <circle cx="{cw/2}" cy="45" r="26" fill="none" stroke="{col}" stroke-width="3" opacity="0.7">
            <animate attributeName="opacity" values="0.5;1;0.5" dur="2.4s" begin="{1.2+i*0.1}s" repeatCount="indefinite"/>
          </circle>
          <text x="{cw/2}" y="53" text-anchor="middle" font-family="'Fira Code',monospace" font-size="20" font-weight="800" fill="{col}">{rank}</text>
          <text x="{cw/2}" y="95" text-anchor="middle" font-family="'Fira Code',monospace" font-size="11" fill="{text_main}">{name}</text>
          <rect width="{cw}" height="140" rx="12" fill="url(#trophyShine)" opacity="0.6">
            <animateTransform attributeName="transform" type="translate" values="-{cw+40},0;{cw+40},0" dur="3s" begin="{2.3+i*0.15}s" repeatCount="indefinite"/>
          </rect>
        </g>''')
    body = f'''
    <defs><linearGradient id="trophyShine" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/><stop offset="50%" stop-color="#ffffff" stop-opacity="0.25"/><stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient></defs>
    {"".join(cells)}
    '''
    return wrap(W, H, body, "trophies")

def main():
    user = api(f"/users/{USERNAME}")
    repos = fetch_all_repos()
    non_forks = [r for r in repos if not r.get("fork")]

    repos_count = user.get("public_repos", len(repos))
    followers = user.get("followers", 0)
    stars = sum(r.get("stargazers_count", 0) for r in repos)

    lang_counts = {}
    for r in non_forks:
        lang = r.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    total = sum(lang_counts.values()) or 1
    lang_pct = sorted(((k, v/total) for k, v in lang_counts.items()), key=lambda x: -x[1])

    stats_svg = build_stats(repos_count, stars, followers)
    langs_svg = build_langs(lang_pct) if lang_pct else None
    trophies_svg = build_trophies(repos_count, stars, followers)

    with open("stats.svg", "w") as f: f.write(stats_svg)
    with open("trophies.svg", "w") as f: f.write(trophies_svg)
    if langs_svg:
        with open("langs.svg", "w") as f: f.write(langs_svg)

    print(f"repos={repos_count} stars={stars} followers={followers}")
    print("top languages:", lang_pct[:5])

if __name__ == "__main__":
    main()
