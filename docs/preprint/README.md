# DART-RIFT. I. — pilot-results preprint

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23284193.svg)](https://doi.org/10.5281/zenodo.23284193)

**Published:** [doi.org/10.5281/zenodo.23284193](https://doi.org/10.5281/zenodo.23284193)
· [Zenodo record](https://zenodo.org/records/23284193)
· [PDF](https://zenodo.org/records/23284193/files/main.pdf?download=1)
· [local build](../../output/pdf/DART-RIFT_Pilot_Results_2026-10-10.pdf)

Cite the version DOI above for this text. The concept DOI
[10.5281/zenodo.23284192](https://doi.org/10.5281/zenodo.23284192) always
resolves to the newest version of the series instead.

## What this reports

Five completed, validity-checked simulations: a three-point cohesion sweep,
one matrix-tension toggle, and one 25 m impact-site offset. The vector
figures are generated from the checked pilot values and the registered
96-point coarse / 12-point fine design. The paper distinguishes these
scene-conditioned findings from a production posterior or a sealed numerical
Hera forecast; neither is reported.

This is Paper I of a two-paper series. Paper II will carry the production
posterior and the numerical Hera predictions if the registered claim gates
pass. They are planned as two separate archival records rather than two
versions of one, since Paper II reports exactly what Paper I declines to
report. Paper II has no identifier yet.

## Building

Everything is generated from source. From this directory, with LuaLaTeX and
the usual TeX packages available:

    make          # every figure, then the paper (twice, for references)
    make veri     # regenerate the data tables from the simulation code

LuaLaTeX rather than pdfLaTeX: the particle-scale figures exhaust pdfLaTeX's
fixed main memory. Sources are `main.tex`, `ethosoft.sty`, `sekil/*.tex` and
`veri/*.dat`; the PDFs are build products and are not tracked.

The repository snapshot under `output/pdf/` is the same file that was
deposited, byte for byte.

## Licensing

The article text and original figures are © 2026 Yağız Ekrem Dalar, Feyzi
Arda Salihoğlu, and Nedim Mutlu Sezer, licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The Ethosoft
logo, ORCID iD icon, and GitHub mark are excluded from that license. The
[ORCID icon](https://info.orcid.org/documentation/integration-guide/orcid-id-display-guidelines/)
and [official GitHub mark](https://brand.github.com/foundations/logo) are
shown under their respective brand guidelines. Repository software remains
under the root [MIT license](../../LICENSE).

The archived measurements and protocol decisions cited in the article are
linked to their source commit.
