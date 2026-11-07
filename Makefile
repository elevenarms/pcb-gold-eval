# pcb-gold-eval: every artefact is rebuilt from pinned inputs (boards.toml, pins.toml) with one command.
# Needs: docker, python3 >= 3.11, uv, node (npx), harbor (for oracle/agent runs).
SHELL := /bin/bash
KICAD := docker run --rm --platform linux/amd64 -v $(CURDIR):/w -w /w $(shell python3 -c "import tomllib;print(tomllib.load(open('pins.toml','rb'))['env']['kicad_image'])")
BOARDS := $(shell python3 -c "import tomllib;print(' '.join(tomllib.load(open('boards.toml','rb'))))")

.PHONY: all fetch meta tasks oracle baselines forecast glb report paper site serve video deploy clean
all: fetch meta tasks forecast report paper site

fetch:            ## download gold boards at pinned commits, verify sha256
	python3 tools/fetch.py

meta: fetch       ## gold DRC, stripped unconnected count, board stats -> data/meta/
	$(KICAD) python3 tools/make_meta.py $(BOARDS)

tasks:            ## generate Harbor tasks -> tasks/route-<id>/
	python3 tools/make_tasks.py

oracle: tasks     ## run the oracle (gold copper) through Harbor: every task must score 1.0
	uvx --from harbor==0.25.0 harbor run -p tasks -a oracle -n 2 -y

baselines: fetch  ## Freerouting baseline sweep -> data/baselines/
	tools/sweep_baselines.sh

forecast:         ## outcome-vs-compute model and charts -> report/m/, site/assets/fig/
	uv run -q --with numpy --with matplotlib python forecast/charts.py

glb: fetch        ## 3D views of the gold boards -> site/assets/glb/
	tools/export_glb.sh

report: forecast  ## Rauchwerk Research field report PDF (also archived to ~/Code/fieldreports)
	npm ci --silent && cd report && python3 build.py && RR_PLAYWRIGHT=$(CURDIR)/node_modules/playwright-core/index.mjs node render.mjs report.html Rauchwerk-Research_PCB-Gold-Master-Eval_Field-Report.pdf

paper: forecast   ## arXiv paper PDF
	python3 paper/gen_tables.py && cd paper && tectonic -X compile --keep-intermediates main.tex

site:             ## fill the data-driven sections of the project page, copy figures and PDFs
	python3 tools/site_fill.py

serve: site       ## serve the project page locally
	cd site && python3 -m http.server 8741

video:            ## explainer video -> site/assets/video/explainer.mp4 (see video/README.md)
	uv run -q --python 3.12 --with kokoro-onnx==0.4.9 --with soundfile python video/tts.py
	npm ci --silent && node video/capture3d.mjs && node video/stills.mjs && python3 -I video/assemble.py

deploy: site      ## deploy the project page (Vercel, static)
	cd site && vercel deploy --prod --yes

clean:
	rm -rf build jobs
