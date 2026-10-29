"""Builds a dark-blue contribution calendar SVG from the GitHub GraphQL API.
Empty days are deep navy; busier days get progressively lighter blue.
Usage: GITHUB_TOKEN=... python scripts/contrib_graph.py <login> <out.svg>
"""
import json, os, sys, urllib.request, datetime

LEVELS = {  # empty -> most commits
    "NONE": "#0B1A33",
    "FIRST_QUARTILE": "#123E7A",
    "SECOND_QUARTILE": "#1E5FB0",
    "THIRD_QUARTILE": "#3D8BEA",
    "FOURTH_QUARTILE": "#9FD3FF",
}
QUERY = """query($login:String!){ user(login:$login){ contributionsCollection{ contributionCalendar{
  totalContributions weeks{ contributionDays{ date contributionCount contributionLevel weekday } } } } } }"""

def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def render(cal):
    CELL, GAP = 11, 3
    STEP = CELL + GAP
    LEFT, TOP = 46, 56
    weeks = cal["weeks"]
    W = LEFT + len(weeks) * STEP + 24
    H = TOP + 7 * STEP + 44
    font = "Segoe UI, Helvetica, Arial, sans-serif"
    cells, months, last_month = [], [], None
    for wi, week in enumerate(weeks):
        x = LEFT + wi * STEP
        for d in week["contributionDays"]:
            y = TOP + d["weekday"] * STEP
            c = LEVELS.get(d["contributionLevel"], LEVELS["NONE"])
            n = d["contributionCount"]
            delay = f' style="animation-delay:{(wi*0.02):.2f}s"' if n else ""
            cls = ' class="lit"' if n else ""
            cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"{cls}{delay}>'
                         f'<title>{n} contribution{"s" if n != 1 else ""} on {d["date"]}</title></rect>')
        first = datetime.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month and first.day <= 7:
            months.append(f'<text x="{x}" y="{TOP-10}" class="lbl">{first.strftime("%b")}</text>')
            last_month = first.month
    days = "".join(f'<text x="{LEFT-10}" y="{TOP + i*STEP + 9}" class="lbl" text-anchor="end">{n}</text>'
                   for i, n in [(1, "Mon"), (3, "Wed"), (5, "Fri")])
    lx = W - 24 - 5 * STEP - 70
    legend = "".join(f'<rect x="{lx + 34 + i*STEP}" y="{H-30}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>'
                     for i, c in enumerate(LEVELS.values()))
    legend = (f'<text x="{lx + 28}" y="{H-21}" class="lbl" text-anchor="end">Less</text>{legend}'
              f'<text x="{lx + 40 + 5*STEP}" y="{H-21}" class="lbl">More</text>')
    total = cal["totalContributions"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#050B18"/><stop offset="1" stop-color="#071431"/></linearGradient>
  <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#4FA3FF" stop-opacity=".35"/><stop offset=".45" stop-color="#4FA3FF" stop-opacity=".35"/>
    <stop offset=".5" stop-color="#E6F3FF" stop-opacity="1"/><stop offset=".55" stop-color="#4FA3FF" stop-opacity=".35"/>
    <stop offset="1" stop-color="#4FA3FF" stop-opacity=".35"/>
    <animateTransform attributeName="gradientTransform" type="translate" from="-1 0" to="1 0" dur="4s" repeatCount="indefinite"/>
  </linearGradient>
  <filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<style>
  .lbl{{font:11px {font};fill:#7FA6D6}}
  .ttl{{font:600 14px {font};fill:#EAF2FF}}
  .lit{{animation:pop .6s ease-out both}}
  @keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}
</style>
<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="12" fill="url(#bg)"/>
<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="12" fill="none" stroke="#4FA3FF" stroke-opacity=".5" stroke-width="2" filter="url(#glow)"/>
<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="12" fill="none" stroke="url(#shine)" stroke-width="1.6"/>
<text x="{LEFT-30}" y="26" class="ttl">✦ {total} contributions in the last year</text>
{''.join(months)}{days}{''.join(cells)}{legend}
</svg>'''

if __name__ == "__main__":
    login, out = sys.argv[1], sys.argv[2]
    if os.environ.get("DEMO"):
        import random; random.seed(1)
        start = datetime.date.today() - datetime.timedelta(days=364)
        start -= datetime.timedelta(days=(start.weekday() + 1) % 7)
        weeks = []
        for w in range(53):
            days = []
            for d in range(7):
                day = start + datetime.timedelta(days=w*7+d)
                n = random.choice([0,0,0,0,1,2,3,5,9])
                lvl = ["NONE","FIRST_QUARTILE","FIRST_QUARTILE","SECOND_QUARTILE","SECOND_QUARTILE","THIRD_QUARTILE","THIRD_QUARTILE","FOURTH_QUARTILE","FOURTH_QUARTILE","FOURTH_QUARTILE"][min(n,9)]
                days.append({"date": day.isoformat(), "contributionCount": n, "contributionLevel": lvl, "weekday": d})
            weeks.append({"contributionDays": days})
        cal = {"totalContributions": 206, "weeks": weeks}
    else:
        cal = fetch(login, os.environ["GITHUB_TOKEN"])
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    open(out, "w").write(render(cal))
    print("wrote", out)
