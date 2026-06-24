import sys, traceback
sys.path.insert(0, '.')
import sqlite3
from verse_engine.config import settings

conn = sqlite3.connect(settings.verse_db_path)
conn.row_factory = sqlite3.Row

try:
    poets = conn.execute("""
        SELECT name, country_code, rep_poem_title as poem_title,
               (score_image + score_voice + score_tension + score_bks + score_body) as total,
               score_image, score_voice, score_tension, score_bks, score_body,
               'storico' as type, era, city
        FROM poet_archive
    """).fetchall()
    print(f"Poeti: {len(poets)}")
    for p in list(poets)[:3]:
        d = dict(p)
        print(f"  {d['name']} — total={d['total']}")

    members = conn.execute("""
        SELECT member_email, NULL as member_display, poem_text,
               (score_image + score_voice + score_tension + score_bks + score_body) as total,
               score_image, score_voice, score_tension, score_bks, score_body,
               'member' as type, submitted_at
        FROM verse_submissions
        WHERE status IN ('approved', 'hall')
        ORDER BY total DESC
        LIMIT 30
    """).fetchall()
    print(f"Members approvati: {len(members)}")

    ranking = []
    for p in poets:
        d = dict(p)
        d["display_name"] = d["name"]
        ranking.append(d)
    for m in members:
        d = dict(m)
        d["display_name"] = d.get("member_display") or d["member_email"].split("@")[0]
        d["poem_title"] = d["poem_text"][:60] + "..." if len(d["poem_text"]) > 60 else d["poem_text"]
        ranking.append(d)

    ranking.sort(key=lambda x: (x["total"] or 0), reverse=True)
    for i, item in enumerate(ranking):
        item["rank"] = i + 1

    print(f"\nTop 3 ranking:")
    for item in ranking[:3]:
        print(f"  #{item['rank']} {item['display_name']} — {item['total']}/25")
    print("\n[OK] Query leaderboard OK")

except Exception as e:
    traceback.print_exc()

conn.close()
