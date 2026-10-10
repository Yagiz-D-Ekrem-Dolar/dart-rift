# Figures and paper for the DART-RIFT pilot preprint.
#   make        -> every figure, then the paper (twice, for references)
#   make veri   -> regenerate the data tables from the simulation code
# lualatex, not pdflatex: the particle-scale figures exhaust pdflatex's
# fixed main memory, and pgfmath underflows below ~1e-5, which is why the
# cascade figure takes decades rather than seconds as its argument.
PY  ?= ../../.venv/Scripts/python.exe
TEX ?= lualatex -interaction=nonstopmode -halt-on-error
SEKILLER = hedef tasarim kapilar butce atlas projeksiyon kacis kaskad paylar duyarlilik
PDFLER   = $(addsuffix .pdf,$(SEKILLER))

all: main.pdf

main.pdf: main.tex ethosoft.sty $(PDFLER)
	$(TEX) main.tex
	$(TEX) main.tex

%.pdf: sekil/%.tex sekil/ortak.tex
	$(TEX) $<

veri:
	cd ../.. && $(PY) scripts/onkayit_veri.py

temiz:
	rm -f *.aux *.log *.out *_on.png sekil/*.aux sekil/*.log

.PHONY: all veri temiz
