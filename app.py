from flask import Flask, render_template, request, session, redirect, url_for
import random
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route("/", methods=["GET", "POST"])
def schedule():
    if request.method == "POST":
        action = request.form.get("action", "")
        players = request.form.getlist("players")
        new_raw = request.form.get("new_players", "")
        delete_players = request.form.getlist("delete_players")

        # 合併新增欄位
        new_players = [p.strip() for p in new_raw.replace("\n", ",").split(",") if p.strip()]
        players += new_players
        players = list(dict.fromkeys(players))  # 去重複
        players = [p for p in players if p not in delete_players]

        session["last_players"] = ",".join(players)
        appearance_count = session.get("appearance_count", {})
        appearance_count = defaultdict(int, appearance_count)

        for name in delete_players:
            if name in appearance_count:
                del appearance_count[name]

        if action == "edit":
            return render_template("form.html", last_players=",".join(players), count=appearance_count)

        if len(players) < 4:
            return render_template("form.html", error="請至少輸入或勾選 4 位選手。", last_players=",".join(players), count=appearance_count)

        # 優先分配給出場次數最少者
        min_count = min([appearance_count[p] for p in players]) if appearance_count else 0
        eligible_players = [p for p in players if appearance_count[p] == min_count]

        for offset in range(1, 5):
            if len(eligible_players) >= 4:
                break
            eligible_players += [p for p in players if appearance_count[p] == min_count + offset]

        eligible_players = list(dict.fromkeys(eligible_players))
        selected_group = random.sample(eligible_players, 4)

        for p in selected_group:
            appearance_count[p] += 1

        session["appearance_count"] = dict(appearance_count)
        session["last_match"] = selected_group

        return render_template("schedule.html", match=selected_group, last_players=",".join(players), count=appearance_count)

    # GET
    last_players = session.get("last_players", "")
    appearance_count = session.get("appearance_count", {})
    return render_template("form.html", last_players=last_players, count=appearance_count)

@app.route("/clear_count", methods=["POST"])
def clear_count():
    players = request.form.getlist("players") or []
    player_str = ",".join(players)
    session["appearance_count"] = {}
    session["last_match"] = []
    return render_template("schedule.html", match=[], last_players=player_str, count={})

@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("schedule"))

if __name__ == "__main__":
    app.run(debug=True)
