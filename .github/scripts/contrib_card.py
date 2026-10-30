# "Year in code" card: the last 12 months of contributions as an animated calendar, in dark and light SVG.
# Stdlib only. Needs a token in GITHUB_TOKEN (the Action's own token is enough). Writes assets/contrib-{dark,light}.svg.
import collections, datetime, json, os, urllib.request

USER = os.environ.get("USERNAME", "Shoaib20786")
Q = """query($u:String!){user(login:$u){contributionsCollection{restrictedContributionsCount
 contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel weekday}}}}}}"""
req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": Q, "variables": {"u": USER}}).encode(),
                             headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"})
cc = json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]["contributionsCollection"]
cal, private = cc["contributionCalendar"], cc["restrictedContributionsCount"]
weeks = cal["weeks"]
days = [d for w in weeks for d in w["contributionDays"]]

# stats
best_streak = cur = 0
for d in days:
    cur = cur + 1 if d["contributionCount"] else 0
    best_streak = max(best_streak, cur)
busiest = max(days, key=lambda d: d["contributionCount"])
months = collections.Counter()
for d in days: months[d["date"][:7]] += d["contributionCount"]
best_month, best_month_n = months.most_common(1)[0]
fmt = lambda iso, f: datetime.date.fromisoformat(iso).strftime(f)

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
THEMES = {"dark": dict(bg="#0b1016", line="#ffffff", line_op=".10", ink="#eef5f7", muted="#9aabb1", acc="#45c2b5",
                       ramp=["#18222a", "#0e4f4a", "#13756c", "#1fa596", "#45c2b5"]),
          "light": dict(bg="#f6f8fa", line="#0f1b2d", line_op=".12", ink="#0f1b2d", muted="#5a6875", acc="#0f766e",
                        ramp=["#e6ecef", "#b6e3dd", "#6cc9bd", "#2a9d8f", "#0f766e"])}
W, H, D, CELL, GAP, X0, Y0 = 900, 300, 10, 12, 3, 62, 132

def card(th):
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{SANS}">'
         f'<rect width="{W}" height="{H}" rx="18" fill="{th["bg"]}"/>'
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{th["line"]}" stroke-opacity="{th["line_op"]}"/>'
         f'<text x="36" y="44" font-size="12" font-weight="700" fill="{th["acc"]}" letter-spacing="2">YEAR IN CODE</text>'
         f'<text x="36" y="80" font-size="30" font-weight="800" fill="{th["ink"]}">{cal["totalContributions"]:,} contributions</text>'
         f'<text x="36" y="104" font-size="13" fill="{th["muted"]}">last 12 months on this account · much of my client work is committed from my company account</text>')
    for i, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        s += f'<text x="{X0 - 10}" y="{Y0 + i * (CELL + GAP) + 10}" text-anchor="end" font-size="10" fill="{th["muted"]}">{lab}</text>'
    seen = set()
    n = len(weeks)
    for wi, w in enumerate(weeks):
        first = w["contributionDays"][0]["date"]
        if first[:7] not in seen and int(first[8:]) <= 7:
            seen.add(first[:7])
            s += f'<text x="{X0 + wi * (CELL + GAP)}" y="{Y0 - 8}" font-size="10" fill="{th["muted"]}">{fmt(first, "%b")}</text>'
        on = round(0.02 + 0.33 * wi / n, 4)  # columns sweep in left to right, hold, then reset for the next loop
        s += (f'<g><animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" calcMode="linear" '
              f'keyTimes="0;{on};{round(on + 0.03, 4)};0.96;1" values="0;0;1;1;0"/>')
        for d in w["contributionDays"]:
            y = Y0 + d["weekday"] * (CELL + GAP)
            s += f'<rect x="{X0 + wi * (CELL + GAP)}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{th["ramp"][LEVEL[d["contributionLevel"]]]}"/>'
        s += "</g>"
    # scanner sweeping across after the reveal, and a pulse on the busiest day
    gw = n * (CELL + GAP)
    s += (f'<rect x="{X0}" y="{Y0 - 4}" width="3" height="{7 * (CELL + GAP) + 4}" rx="1.5" fill="{th["acc"]}" opacity="0">'
          f'<animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" keyTimes="0;0.40;0.42;0.80;0.82;1" values="0;0;.8;.8;0;0"/>'
          f'<animate attributeName="x" dur="{D}s" repeatCount="indefinite" keyTimes="0;0.40;0.82;1" values="{X0};{X0};{X0 + gw};{X0 + gw}"/></rect>')
    bi = next(i for i, w in enumerate(weeks) if busiest in w["contributionDays"])
    bx, by = X0 + bi * (CELL + GAP) + CELL / 2, Y0 + busiest["weekday"] * (CELL + GAP) + CELL / 2
    s += (f'<circle cx="{bx}" cy="{by}" r="8" fill="none" stroke="{th["acc"]}" stroke-width="2" opacity="0">'
          f'<animate attributeName="r" dur="2s" repeatCount="indefinite" values="7;16"/>'
          f'<animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" keyTimes="0;0.38;0.40;0.95;1" values="0;0;.9;.9;0"/></circle>')
    s += (f'<text x="{X0}" y="{H - 22}" font-size="11" fill="{th["muted"]}">Less</text>'
          + "".join(f'<rect x="{X0 + 32 + i * 16}" y="{H - 32}" width="12" height="12" rx="3" fill="{c}"/>' for i, c in enumerate(th["ramp"]))
          + f'<text x="{X0 + 32 + 5 * 16 + 4}" y="{H - 22}" font-size="11" fill="{th["muted"]}">More</text>'
          + f'<text x="{W - 36}" y="{H - 22}" text-anchor="end" font-size="11" fill="{th["muted"]}">updated {datetime.date.today():%d %b %Y}</text>')
    return s + "</svg>"

os.makedirs("assets", exist_ok=True)
for theme, th in THEMES.items():
    open(f"assets/contrib-{theme}.svg", "w").write(card(th))
print(f"contrib card: {cal['totalContributions']} total, streak {best_streak}, busiest {busiest['date']}")
