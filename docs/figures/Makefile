# README figures.
#
#   make          -> every figure, as SVG and PNG
#   make clean    -> remove intermediates (keeps the published SVG/PNG)
#
# lualatex, not pdflatex: the figures share a preamble with the report
# figures, which exhausts pdflatex's fixed main memory.
#
# The SVG is what the README embeds. pdftocairo converts every glyph to a
# path, so the published file carries no font reference and renders the
# same everywhere -- worth checking after a font change:
#
#     grep -c "<text" identifiability.svg     # must print 0
#
# Data comes from the measurement, never from this directory by hand:
#
#     python scripts/tani_esdogrusallik_96.py \
#         docs/sonuclar/havuz_posterior_girdi.csv \
#         --json docs/figures/data/identifiability.json
#     python scripts/figure_data.py

TEX  ?= lualatex -interaction=nonstopmode -halt-on-error
FIGS  = identifiability validation pipeline prediction sensitivity
SVG   = $(addsuffix .svg,$(FIGS))
PNG   = $(addsuffix .png,$(FIGS))

all: $(SVG) $(PNG)

%.pdf: %.tex common.tex
	$(TEX) -jobname $* $<

%.svg: %.pdf
	pdftocairo -svg $< $@

%.png: %.pdf
	pdftocairo -png -r 200 -singlefile $< $*

clean:
	rm -f *.aux *.log *.out

.PHONY: all clean
.PRECIOUS: %.pdf
