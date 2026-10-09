# Figures for the sealed preregistration.
#   make          -> rebuild every figure
#   make veri     -> regenerate the data tables from the code
# lualatex, not pdflatex: the particle-scale figures exhaust pdflatex's
# fixed main memory.
PY  ?= ../../.venv/Scripts/python.exe
TEX ?= lualatex -interaction=nonstopmode -halt-on-error
SEKILLER = hedef tasarim kapilar butce

all: $(addsuffix .pdf,$(SEKILLER))

%.pdf: sekil/%.tex sekil/ortak.tex
	$(TEX) $<

veri:
	cd ../.. && $(PY) scripts/onkayit_veri.py

temiz:
	rm -f *.aux *.log *.out *.pdf *_onizleme.png

.PHONY: all veri temiz
