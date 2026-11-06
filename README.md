<div align="center">

# DART-RIFT

### Reading the interior of an asteroid from the one number DART left behind — and sealing the prediction before Hera arrives to check it.

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.23284193-2198D4?style=flat-square&labelColor=282623)](https://doi.org/10.5281/zenodo.23284193)
[![License](https://img.shields.io/badge/license-MIT-ADA4A4?style=flat-square&labelColor=282623)](LICENSE)
[![Production pool](https://img.shields.io/badge/production%20pool-96%20%2F%2096-2198D4?style=flat-square&labelColor=282623)](docs/sonuclar/havuz_posterior_girdi.csv)
[![Sealed predictions](https://img.shields.io/badge/sealed%20predictions-2-2198D4?style=flat-square&labelColor=282623)](docs/onkayit/)

<br>

<img src="docs/figures/identifiability.svg" width="860" alt="A prior sphere flattened along exactly one axis. The posterior is 0.142 of the prior width along matrix strength and unchanged along the other two interior axes.">

</div>

<br>

## The question

In September 2022, NASA's DART spacecraft struck the asteroid Dimorphos and left
behind **a single number**: the momentum enhancement factor `β`. That number
depends on what the asteroid is made of — a loose rubble pile and a coherent
rocky body do not recoil the same way.

So the obvious move is to run the inference backwards, from `β` to the interior.
But the interior has three unknowns:

| | symbol | what it is |
|---|:---:|---|
| **Boulder porosity** | `α_b` | how much void sits inside the large boulders |
| **Matrix strength** | `Y₀` | cohesive strength of the fine material between them |
| **Boulder fraction** | `f` | how much of the body's volume the boulders occupy |

One scalar cannot determine three numbers. That is not a difficulty to be
engineered away; it is arithmetic. So this project does not ask *"what is the
interior?"* It asks the question that actually has an answer:

> **How many directions of a three-dimensional interior can one scalar
> observation constrain, and which ones?**

It does not guess. It measures.

<br>

## The answer

Across all 96 locked design points of the production campaign, the Fisher
information of the forward model was decomposed and compared against a threshold
fixed before any of the data existed.

| direction | posterior width, relative to prior | verdict |
|---|:---:|---|
| **first** — almost exactly matrix strength `Y₀` | **0.142** | learned |
| second | 0.930 | not learned |
| third | 1.000 | untouched, by rank |

The figure above is that table drawn to scale. The sphere is the prior; the disc
is what remains after the measurement. It is flattened along one axis, and
*nothing at all* happens along the other two.

Three consequences, each measured rather than argued:

**One direction, and it can be named.** The leading eigenvalue clears the locked
threshold at **93 of 96** points. The second clears it **nowhere** — its largest
value anywhere in the design is `33.09`, against a threshold of `36`. The axis
that gets learned is matrix strength: dominant at **90 of 96** points, with a
median share of `0.999` of the learned direction.

**Precision does not rescue it.** Shrinking the observational error by a factor
of 1000 moves the second eigenvalue only from `2.35` to `4.17`. Error bars change
how heavily a row counts, not which way it points. The remedy is not a better
`β`; it is a second observable whose gradient genuinely differs — and the median
angle between the two gradients already available here is `7.95°`.

**This is a statement about the forward model, not about Dimorphos.** The
sensitivity of impact momentum is piled onto one axis. That is why the literature
reports *ranges* for porosity and boulder fraction while constraining strength
more tightly. This work measures the reason.

<br>

## Does the code hold up?

The solver is an independent GPU SPH implementation written for this project:
NVIDIA Warp, FP64, Wendland C2 kernel, Tillotson equation of state, P–α
porosity, Grady–Kipp damage, Barnes–Hut self-gravity. Every GPU kernel has an
independent NumPy FP64 reference and the two are cross-checked, typically
agreeing to better than `1e-8`.

An independent code is worth nothing until it is checked against references it
must reproduce.

| scenario | reference | measured | threshold |
|---|---|---|---|
| Sod shock tube | exact Riemann | shock speed `0.08%`, worst post-shock `0.80%` | 3–5% |
| Sedov–Taylor blast | similarity solution | shock radius `4.46%` | 5% |
| Mass conservation | — | `0.00e+00` | machine precision |
| Momentum conservation | — | `8.39e-16` | `1e-6` |
| Energy conservation | — | `0.432%` | 0.5% |
| Elastic wave speed | `4593 m/s` theoretical | `4458 m/s` → `2.96%` | 3% |
| Taylor bar, copper | experiment `0.60–0.80` | `L/L₀ = 0.731`, energy `0.083%` | 1.5% |

Margins are reported, not hidden: the elastic wave result sits at `2.96%` against
a `3%` threshold. Where a criterion passes narrowly, its behaviour was studied
separately — that error converges to zero with resolution, while the Sedov error
settles onto a floor near `3.9%` that is model-form error rather than
discretisation.

Then the harder test: the same configuration against Bern SPH results published
in *Astronomy & Astrophysics*.

<div align="center">
<img src="docs/figures/validation.svg" width="860" alt="Three matrix strengths compared against Raducan et al. 2022 Table 2. This work lands 13 to 18 percent below the reference, measured on beta minus one.">
</div>

| `Y₀` | this work | Raducan et al. 2022 | ratio on `β − 1` |
|---:|---:|---:|---:|
| 50 Pa | 3.295 | 3.63 | 0.873 |
| 10 Pa | 3.667 | 4.18 | 0.839 |
| 1 Pa | 3.992 | 4.66 | 0.817 |

The trend is reproduced, the locked robustness criterion holds (`≤ 0.20`), and
total energy drifts by `−0.91%` across the run. A fourth independent
implementation landing **13–18% below** a published benchmark is a useful data
point in a field that publishes dedicated code-comparison papers.

<br>

## How it is locked

A result is only worth something if the rules were not chosen after seeing the
answer. They were not.

<div align="center">
<img src="docs/figures/pipeline.svg" width="860" alt="Five stages: design, simulate, observe, infer, seal. Design, infer and seal are marked as having had their decision rules fixed before the data existed.">
</div>

Every marked stage has a protocol document committed **before** the runs it
governs: the design (96 Latin-hypercube points, fixed seed), the posterior recipe
with its identifiability threshold, and the Hera predictions. When a later result
contradicted a hypothesis, the threshold stayed where it was and the hypothesis
was recorded as failed. That is what locking is for.

Two predictions for ESA's Hera mission are sealed with SHA-256 and can be
verified by anyone:

```bash
python scripts/muhur_dogrula.py
```

The verifier is deliberately strict about its own limits. It separates *"the seal
is intact"* from *"the seal is traceable to specific input files"*, and reports
the second as missing where it is missing rather than quietly passing.

<br>

## What this work does not claim

This section matters as much as the results.

- **No point estimate for `(α_b, Y₀, f)`.** The degeneracy is measured. Quoting a
  best-fit triple would be hiding it.
- **No new physics.** The material models are the literature's. The contribution
  is an independent implementation and a measurement of what the inference can
  and cannot recover.
- **Resolution convergence is not achieved.** The locked verdict is
  `NOT CONVERGED`: differences grow as resolution increases. Absolute values are
  therefore not reported as findings; separately-tested contrasts are.
- **Resolution error is a bias, not scatter.** All 7 probe points moved the same
  way, by a factor of `3.22` in `Y₀` (`p = 0.0156`). Folding that into the noise
  term as variance would be wrong, and this is the measurement that says so.
- **Crater depth is structurally unmeasurable here.** In the weak-matrix regime
  the unescaped ejecta covers the crater: the obstruction and the thing being
  measured are the same material. The route was scored against a locked criterion,
  reached `1 of 4`, and was reported as insufficient.
- **The boulder-fraction axis is the weakest.** The production scene generator
  saturates this knob: a requested `0.05 – 0.50` is realised as `0.151 – 0.369`,
  and above `0.436` the scenes are identical. Statements about `f` are bounded by
  that, and the defect is on the record.
- **The target is a fitted ellipsoid, not the PDS shape model.** The official
  shape package was retrieved and verified against its published MD5 checksums,
  but production runs use a triaxial ellipsoid of 88.5 × 87.0 × 58.0 m and
  4.298 × 10⁹ kg.
- **Passing engineering gates is not physical validation.** That the solver
  solves the right equations correctly, and that those equations describe the real
  DART impact, are different claims. The second remains open, and the two tables
  above are kept apart for exactly that reason.

<br>

## Reproduce

Everything on this page regenerates from the repository, with no GPU.

```bash
pip install -e ".[dev]"
```

```bash
python scripts/tani_esdogrusallik_96.py docs/sonuclar/havuz_posterior_girdi.csv --json docs/figures/data/identifiability.json
```

```bash
python scripts/figure_data.py && make -C docs/figures
```

```bash
python scripts/muhur_dogrula.py
```

```bash
python -m pytest -m "not gpu" -q
```

<br>

## Repository

| path | what is in it |
|---|---|
| [`src/dartrift/warp_core/`](src/dartrift/warp_core/) | GPU kernels: kernel function, neighbours, density, forces, integrator, Tillotson, strength, P–α, Grady–Kipp, Barnes–Hut |
| [`src/dartrift/cpu_reference/`](src/dartrift/cpu_reference/) | an independent NumPy FP64 reference for every kernel |
| [`src/dartrift/setup/`](src/dartrift/setup/) | shape, rubble generator, settling, impactor, scene, refinement |
| [`src/dartrift/observables/`](src/dartrift/observables/) | `β`, ejecta catalogue, crater shape, period interface |
| [`src/dartrift/inference/`](src/dartrift/inference/) | design, forward model, surrogate, posterior, history matching |
| [`docs/truba/`](docs/truba/) | 42 locked protocols — decision rules, written before the runs |
| [`docs/adr/`](docs/adr/) | 65 architecture decision records |
| [`docs/defter/`](docs/defter/) | 98 dated records: what was measured, and what failed |
| [`docs/onkayit/`](docs/onkayit/) | sealed Hera predictions, SHA-256 |
| [`docs/sonuclar/`](docs/sonuclar/) | the production pool and the measurements drawn from it |
| [`docs/figures/`](docs/figures/) | the figures on this page and the data behind them |
| [`data_manifest/`](data_manifest/) | retrieved NASA PDS products with verified checksums |

Requirement-to-code-to-test-to-evidence mapping:
[`docs/IZLENEBILIRLIK.md`](docs/IZLENEBILIRLIK.md).
The full engineering record, including every gate report and the complete defect
list, is kept in Turkish: [`docs/README-TR.md`](docs/README-TR.md).

The defect log is public on purpose. Problems are numbered, left visible, and
carry their measurements — including the ones still open. A project that reports
only its successes cannot be checked.

<br>

## Scale

| | |
|---|---:|
| Production design points, all completed | 96 / 96 |
| Locked protocols | 42 |
| Architecture decision records | 65 |
| Dated measurement records | 98 |
| Tests, CPU only | 2,735 |
| Lint violations | 0 |

<br>

## Citation

```bibtex
@software{dartrift,
  title = {DART-RIFT: identifiability of asteroid interior parameters
           from the DART momentum transfer},
  year  = {2026},
  doi   = {10.5281/zenodo.23284193},
  url   = {https://github.com/Yagiz-D-Ekrem-Dolar/dart-rift}
}
```

Released under the [MIT License](LICENSE). This page, the figures and the
preprint are in English; the locked protocols and dated measurement notes are
written in Turkish.
