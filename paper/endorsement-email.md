# Draft: arXiv endorsement request to Byron

**To:** Byron
**Subject:** Would you endorse my first arXiv submission (cs.AR)?

Hi Byron,

I’ve written my first paper and want to put it on arXiv. First-time submitters need an endorsement from someone who has already published in the category, and you were the first person I thought of. Would you be willing?

**The paper:** “Routed Is Not Right: A Gold-Master Benchmark for Machine Routing of High-Frequency Printed Circuit Boards.”

**The short version:** ML routers for circuit boards are scored on wirelength and design-rule checks. Nobody scores what makes a fast board work: impedance-controlled widths, differential-pair skew, length matching. I took eight boards Antmicro has built and open-sourced (PCIe, MIPI, HDMI, DDR4, DDR5), stripped their copper, and score machine routing against the original human layout. I packaged it as an open eval (Harbor format), ran baselines, and added a forecast of what results cost in compute and time. The open-source router finishes most of each board but misses the high-frequency targets.

- **PDF:** attached
- **Code and data:** https://github.com/elevenarms/pcb-gold-eval
- **Project page:** https://pcb-gold-eval.vercel.app

**Category:** cs.AR (Hardware Architecture) as primary, cross-listed to cs.LG. If you publish in a different category that fits better, such as cs.LG or eess.SP, that would work too.

**What it involves:** after I start the submission, arXiv gives me an endorsement code. You enter it at https://arxiv.org/auth/endorse (logged in), which takes about a minute. Endorsing means you’ve looked at the paper and think it’s a reasonable contribution for the category. It isn’t a review, and it doesn’t vouch for every result. If you’d rather read it first, or not do it at all, that’s completely fine.

Happy to walk you through it over coffee.

Thanks,
Dave

---

*Notes for Dave (delete before sending):*
- **Check Byron is eligible.** arXiv only accepts endorsements from authors with enough recent papers in the same subject class. If Byron hasn’t published in cs.AR, ask him to endorse for the category he does publish in, and submit there with cs.AR as a cross-list.
- **Get the code first.** Start the submission at arxiv.org/submit, choose the category, and arXiv will offer “request endorsement” with a six-character code. Paste that code into this email before sending.
- **Upload sources, not just the PDF.** arXiv compiles LaTeX itself: upload `main.tex`, `tables.tex`, `refs.bib`, the generated `main.bbl` and the `fig/` folder. Run `make paper` first.
