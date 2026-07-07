# Veri Güdümlü Polis Karakolu Yerleşim ve Devriye Rotası Optimizasyonu
## Londra · Birmingham (West Midlands) · Chicago — Üç Şehirli Karşılaştırmalı Çalışma

Suç-talep-ağırlıklı **tesis yerleşim optimizasyonu** (p-Median + MCLP) ve gerçek
yol ağı üzerinde **devriye turu rotalama** (Christofides TSP) çalışması.
Üç şehirde, 12'şer aylık gerçek suç kayıtlarının tamamı kullanılarak, mevcut
polis tesislerine kıyasla veri güdümlü yerleşimin hizmet kalitesini ne kadar
artırabileceği nicel olarak gösterilmektedir.

> Projenin eski sürümden (kümeleme/en kısa yol benchmark'ı) bu haline nasıl ve
> neden dönüştürüldüğü için bkz. **[PROJE_NE_OLDU.md](PROJE_NE_OLDU.md)**.

---

## Araştırma sorusu

**Polis karakolu yerleşimi, veri güdümlü optimizasyonla ne kadar daha kaliteli
hale getirilebilir — ve bu kazanç şehirden/ülkeden bağımsız mıdır?**

## Ana bulgular (üç şehir, 12'şer ay, tam veri)

| | **Londra** | **Birmingham (WM)** | **Chicago** |
| :--- | :--- | :--- | :--- |
| Suç kaydı (12 ay) | 1.142.789 | 287.176 | 234.332 |
| Mevcut tesis (OSM) | 148 | 66 | 112 |
| Ort. mesafe: mevcut → p-Median | 1,311 → 0,936 km | 1,588 → 1,051 km | 1,516 → 0,706 km |
| **İyileşme (eşit p)** | **%28,6** | **%33,8** | **%53,5** |
| 3 km kapsama: mevcut → MCLP | %93,9 → %100 | %87,7 → %100 | %97,2 → %100 |
| Mevcut mesafe seviyesi kaç tesisle yakalanır | p=80 (%46 az) | p=40 (%39 az) | p=30 (%73 az) |
| Sezgisel–MILP optimalite açığı | %0,000 | %0,42 | %0,000 |
| Zamansal dış-örneklem açığı | %−0,15 | %1,03 | %0,54 |
| Devriye turu (p=20, gerçek yol) | 202,0 km | 182,4 km | 142,4 km |

Üç farklı şehir morfolojisi ve iki farklı ülkenin veri şemasında aynı yönde,
büyük ve kararlı iyileşme: yöntem **şehirden ve ülkeden bağımsız** çalışmaktadır.
Zamansal doğrulama (ilk 6 ay eğitim → son 6 ay test) yerleşimlerin zamana
dayanıklı olduğunu göstermektedir.

---

## Yöntem

### 1. Talep modeli
- 12 aylık kayıtların tamamı (örnekleme yok), şehir sınır kutusu filtresi.
- Koordinatlar şehre uygun **metrik projeksiyona** dönüştürülür
  (Britanya: EPSG:27700, Chicago: UTM 16N / EPSG:26916).
- Suçlar, **Cambridge Crime Harm Index'ten esinlenen önem ağırlıklarıyla**
  (şiddet 10 · soygun/silah 8 · konut hırsızlığı 5 · … · asayiş 1; Chicago
  kategorileri aynı ölçeğe eşlenmiştir) ağırlıklandırılır ve **500 m ızgara
  hücrelerinde** toplulaştırılır.
- Aday tesis konumları: şehre yayılı **1 km ızgara** hücreleri.

### 2. Optimizasyon modelleri

| Model | Amaç fonksiyonu | Çözüm |
| :--- | :--- | :--- |
| **p-Median** | min Σᵢ wᵢ · min_{j∈S} d(i,j), \|S\| = p | Açgözlü kurulum + **Teitz-Bart** yerel arama |
| **p-Median (kesin)** | aynı | **PuLP / CBC MILP** — sezgiselin optimalite açığını doğrular |
| **MCLP** | max Σᵢ wᵢ zᵢ; zᵢ ≤ Σ_{j: d≤3km} yⱼ; Σyⱼ = p | Açgözlü (1−1/e garantili) + **kesin MILP** |
| **Devriye turu** | kapalı tur uzunluğu | **Christofides** (≤1,5·OPT) — gerçek OSM yol-ağı mesafeleriyle; MST alt sınır olarak raporlanır |

### 3. Kıyas ve doğrulama
- **Mevcut durum kıyası:** her şehirde OSM'den gerçek polis tesisleri
  (`amenity=police`) çekilir ve aynı metriklerle değerlendirilir.
- **Metrikler:** talep-ağırlıklı ortalama/medyan/maksimum mesafe; 1/2/3/5 km
  yarıçaplarda kapsanan talep yüzdesi.
- **Zamansal dış-örneklem doğrulama:** ilk 6 ayda seçilen yerleşim, son 6 ayın
  talebiyle test edilir ve test döneminin kendi optimumuyla kıyaslanır.
- **p duyarlılık analizi:** 13 senaryo ile karakol sayısı ↔ hizmet kalitesi
  ödünleşim eğrileri.

---

## Dizin yapısı

```
polis_optimizasyon.py     # tüm pipeline (çok-şehirli)
data/
  london/                 # police.uk aylık CSV'leri (Metropolitan + City of London)
  west-midlands/          # police.uk aylık CSV'leri
  chicago/                # Chicago Data Portal (SODA API) CSV'si
sonuclar/
  <şehir>/                # her şehrin çıktıları:
    optimizasyon_haritasi.html    # interaktif harita (ısı + mevcut/önerilen + devriye)
    p_duyarlilik_analizi.png/.csv
    kapsama_karsilastirmasi.png
    dis_orneklem_dogrulama.png
    metrik_ozet.csv
    optimum_karakol_konumlari.csv
    devriye_turu.csv
```

## Veri kaynakları

| Şehir | Kaynak | Erişim |
| :--- | :--- | :--- |
| Londra, West Midlands | police.uk açık veri arşivi | `https://data.police.uk/data/archive/latest.zip` (aylık `*-street.csv` dosyaları `data/<şehir>/` altına) |
| Chicago | Chicago Data Portal (SODA API) | `https://data.cityofchicago.org/resource/ijzp-q8t2.csv?$select=date,primary_type,latitude,longitude&$where=...` |
| Mevcut karakollar + yol ağları | OpenStreetMap | çalışma anında `osmnx` ile otomatik |

## Kurulum ve çalıştırma

```bash
pip install numpy pandas scikit-learn networkx matplotlib folium osmnx pyproj pulp

python polis_optimizasyon.py london          # tek şehir
python polis_optimizasyon.py chicago
python polis_optimizasyon.py all             # üç şehir sırayla
```

- **İnternet:** mevcut karakollar ve yol ağı OSM'den indirilir (önbelleklenir).
  Erişim yoksa program kuş uçuşu mesafeye düşerek kesintisiz devam eder.
- **Süre:** Londra ~15 dk, Birmingham ~4 dk, Chicago ~2 dk (ilk koşumda yol ağı
  indirme dahil). **PuLP** yoksa kesin MILP doğrulaması atlanır.

## Kısıtlar

- OSM `amenity=police` etiketi küçük polis noktalarını da içerebilir; resmi
  tesis listeleriyle çapraz doğrulama gelecek çalışmadır.
- Yerleşim fazında mesafeler projeksiyonlu Öklid'dir (devriye fazında gerçek yol
  ağı kullanılır).
- Tesis kurulum maliyeti, kapasite ve personel kısıtları modellenmemiştir.
- Devriye turu/MST oranındaki 1,5 garantisi TSP optimumuna göredir; MST'ye göre
  oran 1,5'i marjinal aşabilir.

## Lisans

MIT — bkz. [LICENSE](LICENSE).
