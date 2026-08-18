# Güvenlik

DART-RIFT bir araştırma yazılımı: ağ hizmeti sunmaz, kimlik doğrulaması
yapmaz, kullanıcı verisi işlemez. Saldırı yüzeyi buna göre dardır.

## Bildirim

Bir güvenlik sorunu bulursanız **herkese açık issue açmayın**. GitHub'ın
[özel güvenlik bildirimi](https://docs.github.com/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
akışını kullanın.

Yanıt hedefi: **7 gün** içinde ilk dönüş.

## Kapsam

Gerçek kabul edilenler:

- Bağımlılıklardaki (NumPy, h5py, PyYAML, Pydantic, Warp) bilinen açıklar.
- Güvenilmeyen bir dosyanın işlenmesiyle kod çalıştırılması —
  özellikle `configs/*.yaml`, HDF5 çıktıları ve PDS şekil modelleri.
- CI'da gizli sızdıran veya keyfi kod çalıştıran bir yol.

Kapsam **dışı**:

- Yanlış fizik sonuçları. Bunlar güvenlik değil **doğruluk** sorunudur;
  `Fizik regresyonu` issue şablonunu kullanın.
- Kullanıcının kendi makinesinde kendi kodunu çalıştırması.

## Bilinen ve kabul edilen

- **HPC kimlik bilgileri depoya girmez.** TRUBA erişimi kullanıcının
  kendi ortamındadır; hiçbir parola, anahtar veya oturum bilgisi bu
  depoda tutulmaz ve commit edilmez.
- **Warp CUDA çekirdekleri derler.** Güvenilmeyen bir kaynaktan gelen
  çekirdek kodu çalıştırmayın.

## Desteklenen sürümler

Yalnızca `main`. Bu bir araştırma deposu; yayınlanmış sürümler için
geriye dönük güvenlik yaması sözü verilmiyor.
