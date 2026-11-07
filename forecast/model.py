"""Outcome forecast model: gold-relative rubric score vs compute budget ($) and wall clock (h).
Score G in [0,1]: 1.0 = matches the human gold master (Antmicro layout) on every rubric item.
Each strategy: fixed cost (data/training) then a saturating return in effective evaluations:
   G(N) = Gmax - (Gmax - G0) * (1 + N/N0)^(-alpha)
N = effective evals = min(budget_left / cost_per_eval, hours_left * P / t_eval)
All parameters are ASSUMPTIONS, anchored where possible (see notes)."""
import numpy as np
CPU = 0.047   # $/core-h, Modal (fetched 2026-11-07); AWS c7g spot ~0.016
GPU = 2.50    # $/GPU-h, A100-80 Modal; RunPod community 1.19-1.39
P_CPU = 256   # parallel cores assumed available (one Modal app / small fleet)
P_GPU = 8
# name, G0, Gmax, N0, alpha, t_eval_h (per eval, core-h), $/eval, fixed $, fixed hours, kind
S = {
 "Multi-start router":        dict(G0=.45, Gmax=.66, N0=8,    a=.55, t=60/3600,  c=CPU*60/3600,  F=0,    FT=0,   P=P_CPU),
 "Evolved placement + router": dict(G0=.45, Gmax=.80, N0=600,  a=.60, t=120/3600, c=CPU*120/3600, F=0,    FT=0,   P=P_CPU),
 "+ SI surrogate (openEMS)":  dict(G0=.45, Gmax=.88, N0=900,  a=.60, t=125/3600, c=CPU*125/3600, F=150,  FT=10,  P=P_CPU),
 "LLM-evolved heuristics":    dict(G0=.45, Gmax=.86, N0=250,  a=.55, t=0.35,     c=0.35*CPU*16+0.30, F=0, FT=0, P=32),
 "Learned policy (RL/GNN)":   dict(G0=.45, Gmax=.92, N0=2.5e5,a=.70, t=30/3600,  c=CPU*30/3600+GPU*30/3600/64, F=900, FT=36, P=P_CPU),
}
def G(s, B, T):
    p = S[s]; B = np.asarray(B, float); T = np.asarray(T, float)
    Bl = np.clip(B - p["F"], 0, None); Tl = np.clip(T - p["FT"], 0, None)
    N = np.minimum(Bl / p["c"], Tl * p["P"] / p["t"])
    g = p["Gmax"] - (p["Gmax"] - p["G0"]) * (1 + N / p["N0"]) ** (-p["a"])
    return np.where((B >= p["F"]) & (T >= p["FT"]), g, p["G0"])
def best(B, T):
    vals = np.stack([G(s, B, T) for s in S]); return vals.max(0), vals.argmax(0)
if __name__ == "__main__":
    for B in (10, 100, 1000, 10000):
        print(B, [round(float(G(s, B, 24)), 3) for s in S])
