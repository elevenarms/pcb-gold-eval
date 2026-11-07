"""Forecast charts from forecast.toml -> report/m/*.png, site/assets/fig/*.png, forecast/forecast.json.
Monochrome (Rauchwerk Research house style): strategies are told apart by grey level, dash and direct labels."""
import json, pathlib, tomllib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm, colors

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = tomllib.loads((ROOT / "forecast/forecast.toml").read_text())
OUT = [ROOT / "report/m", ROOT / "site/assets/fig", ROOT / "paper/fig"]
for o in OUT:
    o.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 8, "axes.edgecolor": "#0a0a0a", "axes.linewidth": .8,
                     "xtick.color": "#555553", "ytick.color": "#555553"})
P, E = CFG["prices"], CFG["eval"]
S = CFG["strategy"]
STYLE = {"agent": ("#a4a4a2", "-."), "multistart": ("#b9b9b6", "-"), "evolved": ("#7a7a78", "-"), "si_tools": ("#3d3d3b", "-"),
         "surrogate": ("#0a0a0a", "-"), "llm_evolve": ("#555553", "--"), "rl": ("#8a8a88", ":")}


TIER = "medium"


def G(k, B, T, tier=None):
    s, t = S[k], CFG["tier"][tier or TIER]
    B, T = np.asarray(B, float), np.asarray(T, float)
    core_h = t["route_core_h"] + s.get("em_frac", 0) * t["em_core_h"]          # core-hours per candidate
    par = s.get("parallel_override", E["parallel_cores"])
    wall_h = s.get("h_per_eval_override", core_h)                              # hours per candidate on one worker
    usd = core_h * P["cpu_core_h"] + s.get("usd_per_eval_extra", 0.0)
    fu = t["surrogate_usd"] if s.get("surrogate_fixed") else s.get("fixed_usd", 0)
    fh = t["surrogate_h"] if s.get("surrogate_fixed") else s.get("fixed_h", 0)
    Bl, Tl = np.clip(B - fu, 0, None), np.clip(T - fh, 0, None)
    N = np.minimum(Bl / usd, Tl * par / wall_h)
    g = s["g0"] + (s["gmax"] - s["g0"]) * (1 - (1 + N / s["n0"]) ** (-s["alpha"]))
    return np.where((B >= fu) & (T >= fh), g, s["g0"])


def envelope(B, T):
    v = np.stack([G(k, B, T) for k in S])
    return v.max(0), v.argmax(0)


def save(fig, name):
    for o in OUT:
        fig.savefig(o / name, dpi=220)
    plt.close(fig)


def lines(x, ys, xlabel, name, note):
    f, ax = plt.subplots(figsize=(6.6, 2.9))
    ends = sorted(((float(y[-1]), k) for k, y in ys.items()))
    pos, last = {}, -1
    for yv, k in ends:                       # dodge end labels: keep >= 0.05 apart
        last = max(yv, last + 0.05); pos[k] = last
    for k, y in ys.items():
        c, ls = STYLE[k]
        ax.plot(x, y, c=c, ls=ls, lw=1.8 if k == "surrogate" else 1.4)
        ax.text(x[-1] * 1.08, pos[k], S[k]["label"] + ("  (unproven)" if S[k]["evidence"] == "unproven" else ""),
                va="center", fontsize=7, color="#0a0a0a" if k == "surrogate" else "#555553")
    ax.set_xscale("log"); ax.set_ylim(0, 1); ax.set_xlim(x[0], x[-1])
    ax.set_xlabel(xlabel, color="#555553"); ax.set_ylabel("forecast eval reward (1 = human gold)", color="#555553")
    ax.axhline(1, c="#0a0a0a", lw=.6, ls=(0, (1, 2))); ax.text(x[0] * 1.1, 0.965, "human gold master", fontsize=6.5, color="#555553")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", c="#d6d6d3", lw=.6); ax.set_axisbelow(True)
    ax.text(x[0] * 1.1, 0.04, note, fontsize=6.5, color="#8a8a88")
    f.subplots_adjust(left=.09, right=.72, bottom=.16, top=.97)
    save(f, name)


ALL = {}
for TIER in CFG["tier"]:
    B = np.logspace(1, 5, 200)       # $10 .. $100k
    T = np.logspace(np.log10(0.25), np.log10(336), 200)   # 15 min .. 2 weeks
    lines(B, {k: G(k, B, 24.0) for k in S}, "compute budget per board (USD, log)", f"fc_budget_{TIER}.png", "wall clock fixed at 24 h")
    lines(T, {k: G(k, 1000.0, T) for k in S}, "wall clock (hours, log)", f"fc_time_{TIER}.png", "budget fixed at $1,000")

    # 3D surface of the best achievable reward
    lb, lt = np.meshgrid(np.linspace(1, 5, 90), np.linspace(np.log10(0.25), np.log10(336), 90))
    Z, W = envelope(10 ** lb, 10 ** lt)
    f = plt.figure(figsize=(6.6, 4.4))
    ax = f.add_subplot(projection="3d", computed_zorder=False)
    norm = colors.Normalize(0.1, 0.95)
    greys = matplotlib.colormaps["Greys"]
    ax.plot_surface(lb, lt, Z, facecolors=greys(norm(Z) * .85 + .1), rstride=2, cstride=2, linewidth=.15, edgecolor="#f2f2f0",
                    antialiased=True, shade=False)
    ax.contour(lb, lt, Z, levels=[.3, .5, .7, .8], zdir="z", offset=0, colors="#555553", linewidths=.6)
    ax.set_zlim(0, 1)
    ax.set_xticks([1, 2, 3, 4, 5]); ax.set_xticklabels(["$10", "$100", "$1k", "$10k", "$100k"])
    ax.set_yticks(np.log10([0.25, 1, 4, 24, 168])); ax.set_yticklabels(["15 min", "1 h", "4 h", "1 day", "1 week"])
    ax.set_zticks([0, .25, .5, .75, 1])
    ax.set_xlabel("budget", color="#555553", labelpad=2); ax.set_ylabel("wall clock", color="#555553", labelpad=4)
    ax.set_zlabel("reward", color="#555553", labelpad=0)
    ax.view_init(elev=24, azim=-128)
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.set_pane_color((0.95, 0.95, 0.94, 1)); a._axinfo["grid"]["color"] = "#d6d6d3"; a._axinfo["grid"]["linewidth"] = .5
    f.subplots_adjust(left=0, right=1, bottom=0, top=1)
    save(f, f"fc_surface3d_{TIER}.png")

    # winner map (which strategy is best where)
    f, ax = plt.subplots(figsize=(6.6, 2.6))
    keys = list(S)
    cmap = colors.ListedColormap([STYLE[k][0] for k in keys])
    ax.pcolormesh(10 ** lb, 10 ** lt, W, cmap=cmap, vmin=-.5, vmax=len(keys) - .5, shading="auto")
    cs = ax.contour(10 ** lb, 10 ** lt, Z, levels=[.3, .5, .7, .8], colors="#f2f2f0", linewidths=.7)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("compute budget per board (USD)", color="#555553"); ax.set_ylabel("wall clock (h)", color="#555553")
    for k in keys:
        m = W == keys.index(k)
        if m.sum() > 40:
            ax.text(10 ** np.median(lb[m]), 10 ** np.median(lt[m]), S[k]["label"], fontsize=6.8, ha="center", va="center",
                    color="#f2f2f0" if STYLE[k][0] in ("#0a0a0a", "#3d3d3b", "#555553") else "#0a0a0a")
    f.subplots_adjust(left=.09, right=.98, bottom=.17, top=.97)
    save(f, f"fc_winner_{TIER}.png")

    # budget table for recommendations
    rows = []
    for b in (100, 1_000, 10_000):
        for t in (4, 24, 168):
            z, w = envelope(np.array(b), np.array(t))
            rows.append(dict(budget=b, hours=t, reward=round(float(z), 3), best=S[keys[int(w)]]["label"]))
    ALL[TIER] = dict(rows=rows, curves={k: dict(budget=[round(float(v), 4) for v in G(k, B, 24.0)][::10]) for k in S})
    for r in rows:
        print(TIER, r)

json.dump(ALL, open(ROOT / "forecast/forecast.json", "w"), indent=1)
