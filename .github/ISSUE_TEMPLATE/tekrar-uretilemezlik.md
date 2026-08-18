---
name: Tekrar üretilemezlik
about: Aynı girdi aynı çıktıyı vermiyor
labels: determinizm
---

> ADR-0004 belirlenimci kayan nokta politikasını kilitliyor. Bu şablon
> tam o kilidin kırıldığı durumlar için.

## Fark

| | |
|---|---|
| iki koşu arasındaki fark (mutlak / göreli) | |
| bit düzeyinde mi, yoksa `1e-14` mertebesinde mi | |
| aynı makinede mi, iki makine arasında mı | |
| CPU↔GPU arasında mı | |

## Yeniden üretme

```bash
# iki koşu, tam komut
```

## Altın hash

- [ ] `pytest tests/test_determinism_golden.py` **düşüyor**
- [ ] Altın hash geçiyor ama başka bir yerde fark var (nerede:)
