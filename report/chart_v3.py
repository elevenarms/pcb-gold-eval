import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, datetime as dt
plt.rcParams.update({"font.family":"Helvetica Neue","font.size":8,"axes.edgecolor":"#0a0a0a","axes.linewidth":.8})
rows=[l.split() for l in open("v3curve.txt")]
t0=dt.datetime.fromisoformat(rows[0][0])
xs=[(dt.datetime.fromisoformat(a)-t0).total_seconds()/3600 for a,_,_ in rows]; ys=[int(c) for *_,c in rows]
best=[];b=10**9
for y in ys: b=min(b,y); best.append(b)
f,ax=plt.subplots(figsize=(6.6,2.35),dpi=220)
yy=[max(y,.6) for y in ys]; bb=[max(y,.6) for y in best]
ax.scatter(xs,yy,s=9,c="#b9b9b6",zorder=2,label="each DRC check")
ax.step(xs,bb,where="post",c="#0a0a0a",lw=1.6,zorder=3)
ax.set_yscale("log"); ax.set_yticks([.6,1,10,100,499]); ax.set_yticklabels(["0","1","10","100","499"])
ax.set_xlabel("hours after first routed DRC check (06 Nov 04:20 UTC)",color="#555553")
ax.set_ylabel("unconnected items",color="#555553")
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.grid(axis="y",c="#d6d6d3",lw=.6); ax.set_axisbelow(True)
ax.annotate("rebuilds reset to 499",(0.72,499),(1.35,330),fontsize=7,color="#555553",arrowprops=dict(arrowstyle="-",color="#8a8a88",lw=.6))
ax.annotate("92% gone in 22 min",(0.37,41),(1.2,48),fontsize=7,color="#0a0a0a",arrowprops=dict(arrowstyle="-",color="#0a0a0a",lw=.6))
ax.annotate("last item: 2.5 h",(3.6,1),(3.0,3.2),fontsize=7,color="#0a0a0a",arrowprops=dict(arrowstyle="-",color="#0a0a0a",lw=.6))
ax.text(xs[-1],1.0,"best so far",fontsize=7,ha="right",va="bottom",color="#0a0a0a")
plt.tight_layout(); plt.savefig("m/v3curve.png")
print(xs[-1], [(round(x,2),y) for x,y in zip(xs,best)][::6])
