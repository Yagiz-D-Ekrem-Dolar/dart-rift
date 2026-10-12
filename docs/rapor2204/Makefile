# TÜBİTAK 2204 proje raporu ve şekilleri.
#   make        -> her şekil, sonra rapor (çapraz başvurular için iki kez)
#   make temiz  -> ara dosyaları sil
#
# lualatex, pdflatex DEĞİL: parçacık ölçekli şekiller pdflatex'in sabit ana
# belleğini tüketiyor ve pgfmath ~1e-5'in altında taşıyor.
#
# Veri üretilmiyor: `../preprint/veri/*.dat` tek kaynaktır ve
# `scripts/onkayit_veri.py` ile üretilir (bkz. ../preprint/Makefile veri).
TEX ?= lualatex -interaction=nonstopmode -halt-on-error
SEKILLER = hedef kaskad tasarim kapilar bulgular atlas duyarlilik
PDFLER   = $(addsuffix .pdf,$(SEKILLER))

all: rapor.pdf

rapor.pdf: rapor.tex tubitak.sty $(PDFLER)
	$(TEX) rapor.tex
	$(TEX) rapor.tex

%.pdf: sekil/%.tex sekil/ortak.tex
	$(TEX) $<

temiz:
	rm -f *.aux *.log *.out sekil/*.aux sekil/*.log

.PHONY: all temiz
