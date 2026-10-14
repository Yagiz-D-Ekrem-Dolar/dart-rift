# TÜBİTAK 2204 proje raporu ve şekilleri.
#   make        -> her şekil, sonra rapor (çapraz başvurular için iki kez)
#   make temiz  -> ara dosyaları sil
#
# lualatex, pdflatex DEĞİL: parçacık ölçekli şekiller pdflatex'in sabit ana
# belleğini tüketiyor ve pgfmath ~1e-5'in altında taşıyor.
#
# Veri üç kaynaktan gelir, hiçbiri burada kopyalanmaz:
#   ../preprint/veri/*.dat   sahne, pilot, tasarım  (scripts/onkayit_veri.py)
#   veri/{cekirdek,lundborg,crush}.dat  malzeme     (make veri)
#   veri/eksen_duyarliligi.dat  havuz ölçümü        (TRUBA, KAYIT-078)
PY  ?= ../../.venv/Scripts/python.exe
TEX ?= lualatex -interaction=nonstopmode -halt-on-error
SEKILLER = dejenerasyon cekirdek malzeme hedef kaskad tasarim \
           kapilar bulgular atlas duyarlilik eksen
PDFLER   = $(addsuffix .pdf,$(SEKILLER))

all: rapor.pdf

rapor.pdf: rapor.tex tubitak.sty $(PDFLER)
	$(TEX) rapor.tex
	$(TEX) rapor.tex

%.pdf: sekil/%.tex sekil/ortak.tex
	$(TEX) $<

# Malzeme eğrilerini koddaki formülden yeniden üret. Havuz ölçümü
# (eksen_duyarliligi.dat) buna dâhil DEĞİL -- o TRUBA'dan gelir.
veri:
	cd ../.. && $(PY) scripts/rapor2204_veri.py

temiz:
	rm -f *.aux *.log *.out sekil/*.aux sekil/*.log

.PHONY: all veri temiz
