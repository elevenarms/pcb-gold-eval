def mark(active, dark=False, numbered=True):
    sq = {1: (30, 32, 106, 96), 2: (30, 155, 106, 100), 3: (30, 285, 106, 100), 4: (272, 32, 106, 96)}
    out = []
    for n, (x, y, w, h) in sq.items():
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{"#fff" if n == active else "#3a3a3a"}"/>')
        if n == active and numbered:
            out.append(f'<text x="{x + w/2}" y="{y + h/2 + 22}" text-anchor="middle" font-family="Helvetica Neue,Inter,Arial" font-weight="800" font-size="62" fill="#000">{n}</text>')
    stroke = ' stroke="#fff" stroke-width="10"' if dark else ""
    return f'<svg viewBox="0 0 410 410"><rect width="410" height="410" fill="#0a0a0a"{stroke}/>{"".join(out)}</svg>'

def page(n, chap, body):
    return f'''<section class="page">
<div class="topline"><span>{chap}</span><span>{DOC}</span></div>
<div class="foot"><span class="bug"><img src="assets/mark-black.png">Rauchwerk Research</span><span>Dave Rauchwerk · {DATE}</span><span>{n:02d} / {TOT:02d}</span></div>
<div class="body">{body}</div></section>'''

def chead(n, kicker, title):
    return f'<div class="chead">{mark(n)}<div><div class="kicker">{kicker}</div><h2>{title}</h2></div></div>'

TAG = {"ok": "Works well", "grow": "Refine", "next": "Coming soon"}
def tag(k): return f'<span class="tag {k}">{TAG[k]}</span>'
