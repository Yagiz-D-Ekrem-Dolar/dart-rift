# Build the research preprint and its three vector figures.
# Run from docs/preprint. MiKTeX may need --disable-installer in offline mode.
PY  ?= ../../.venv/Scripts/python.exe
TEX ?= lualatex --disable-installer -interaction=nonstopmode -halt-on-error

all: main.pdf

main.pdf: main.tex sekil/ethosoft-logo.png sekil/orcid-id.png sekil/github-invertocat.pdf tasarim.pdf sekil/bulgular.pdf sekil/kaciklik.pdf
	$(TEX) main.tex
	$(TEX) main.tex

tasarim.pdf: sekil/tasarim.tex veri/tasarim_kaba.dat veri/tasarim_ince.dat
	$(TEX) sekil/tasarim.tex

sekil/bulgular.pdf: sekil/bulgular.tex veri/bulgular_do.dat
	$(TEX) -output-directory=sekil sekil/bulgular.tex

sekil/kaciklik.pdf: sekil/kaciklik.tex veri/kaciklik.dat veri/bulgular_do.dat
	$(TEX) -output-directory=sekil sekil/kaciklik.tex

veri:
	cd ../.. && $(PY) scripts/onkayit_veri.py

.PHONY: all veri
