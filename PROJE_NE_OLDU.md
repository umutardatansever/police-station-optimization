# PROJE NE OLDU? — Dönüşüm Raporu

> **Güncelleme (7 Temmuz 2026):** Proje üç şehre genişletildi — bkz. Bölüm 8.
> "Tek şehir + tek ay" kısıtı tamamen kapatıldı: Londra ve West Midlands için
> 12'şer aylık police.uk verisi, Chicago için 12 aylık Chicago Data Portal
> verisi eklendi; pipeline çok-şehirli hale getirildi
> (`python polis_optimizasyon.py all`). Güncel üç şehirli sonuç tablosu
> README'dedir.

> **Tarih:** 6 Temmuz 2026
> **Amaç:** Projeyi ders projesi seviyesinden, Q1/Q2 dergilere aday gösterilebilecek
> bir araştırma çalışmasına dönüştürmek. Ana araştırma sorusu:
> **"Londra'daki polis karakolu yerleşimi veri güdümlü optimizasyonla ne kadar
> daha kaliteli hale getirilebilir?"**

---

## 1. Eski proje neydi, neden yetmiyordu?

Eski proje (`sucpy.py`), ders kitabı algoritmalarının (K-Means, DBSCAN, Dijkstra,
A*, Prim) tek bir veri seti üzerinde süre/bellek kıyasını yapan bir **benchmark
çalışmasıydı**. Q1/Q2 hakemlerinin ilk itirazları şunlar olurdu:

- "K-Means centroid'i = karakol" varsayımı metodolojik olarak zayıf; karakol
  konumlandırma literatürde **tesis yerleşim problemi** (p-median, MCLP) olarak
  formüle edilir, kümeleme problemi olarak değil.
- 15 düğümlü küçük bir çizgede Dijkstra ile A* süre kıyası bilinen bir sonuçtur,
  alana katkı içermez.
- Değerlendirme metrikleri (algoritma kaç saniyede çalıştı) alan-anlamlı değildi;
  dergiler **hizmet kalitesi** metriklerini (kapsama, erişim mesafesi) ister.
- Gerçek dünya kıyası (mevcut karakollar) yoktu — "önerilen yerleşim neye göre
  iyi?" sorusu cevapsızdı.

## 2. Yeni proje nedir?

Tek ana program: **`polis_optimizasyon.py`**. Proje artık bir
**suç-talep-ağırlıklı tesis yerleşim ve devriye rotalama çalışması**:

### 2.1 Talep modeli
- 93.871 gerçek suç kaydının **tamamı** kullanılıyor (örnekleme yok).
- Koordinatlar **EPSG:27700 (British National Grid)** metrik projeksiyona
  dönüştürülüyor (enlem/boylamda Öklid mesafesi hatasından kurtulundu — eski
  projenin bir diğer metodolojik zaafı).
- Suçlar **Cambridge Crime Harm Index'ten esinlenen önem ağırlıklarıyla**
  (şiddet 10, soygun/silah 8, hırsızlık 1 vb.) ağırlıklandırılıp **500 m
  ızgara hücrelerinde** toplulaştırılıyor → 5.080 talep düğümü.
- Aday tesis konumları: tüm şehre yayılı 1 km ızgara → 1.593 aday.

### 2.2 Optimizasyon modelleri (projenin yeni çekirdeği)
| Model | Amaç | Çözüm yöntemi |
| :--- | :--- | :--- |
| **p-Median** | Talep-ağırlıklı ortalama erişim mesafesini minimize et | Açgözlü kurulum + **Teitz-Bart** yerel arama; **PuLP/CBC kesin MILP** ile doğrulama |
| **MCLP** (Maximal Covering Location Problem) | 3 km yarıçapta kapsanan talebi maksimize et | Açgözlü (1−1/e garantili) + **kesin MILP** (optimal) |
| **Christofides TSP** | Karakollar arası kapalı devriye turu (≤1,5·OPT garantili) | Gerçek OSM yol ağı mesafeleriyle, MST alt sınırıyla birlikte |

### 2.3 Gerçek dünya kıyası
OpenStreetMap'ten Londra'daki **148 gerçek polis tesisi** (`amenity=police`)
çekilip aynı metriklerle değerlendiriliyor. Böylece "önerilen yerleşim mevcut
duruma göre ne kazandırır?" sorusu **nicel** olarak cevaplanıyor.

### 2.4 Deneysel doğrulama katmanları
- **Optimalite doğrulaması:** Sezgisel çözüm, kaba örneklemde kesin MILP
  optimumuyla kıyaslanıyor (açık raporlanıyor).
- **Dış-örneklem doğrulama:** Veri ikiye bölünüp yarıda "eğitilen" yerleşim
  diğer yarıda test ediliyor (veri çok aylıysa zamansal bölme otomatik devreye
  girer; mevcut veri tek ay — 2025-11 — olduğundan rastgele yarı-bölme kullanıldı).
- **p duyarlılık analizi:** 5–148 arası 13 senaryo ile karakol sayısı ↔ hizmet
  kalitesi ödünleşim eğrisi.

## 3. Ana bulgular (son koşum, 6 Temmuz 2026)

Mevcut 148 tesise karşı **eşit sayıda tesisle**:

| Metrik | Mevcut karakollar | p-Median (önerilen) | MCLP (önerilen) |
| :--- | :--- | :--- | :--- |
| Talep-ağırlıklı ort. mesafe | 1,310 km | **0,927 km (%29,3 iyileşme)** | 1,672 km |
| 3 km kapsama (talep %) | %93,7 | %99,4 | **%100,0** |
| 1 km kapsama (talep %) | %45,5 | **%60,9** | %20,4 |

- **Eşdeğer hizmet, çok daha az tesisle:** Mevcut ortalama mesafe seviyesi
  optimize yerleşimle **p=80** karakolda (%46 daha az tesis), mevcut 3 km
  kapsama seviyesi **p=60** karakolda (%59 daha az tesis) yakalanıyor.
  *(Makalenin ana çarpıcı bulgusu budur.)*
- **Teitz-Bart sezgiseli, kesin MILP optimumunu buldu** (optimalite açığı %0,000)
  — büyük örneklemde sezgisel kullanmanın meşruiyetini kanıtlıyor.
- **Dış-örneklem açığı yalnızca %0,79** — yerleşim örneklem gürültüsüne karşı
  kararlı.
- **Devriye turu (p=20 senaryosu):** gerçek yol ağında (105.946 düğüm) 216,6 km
  kapalı tur; MST alt sınırı 152,7 km (oran 1,42 ≤ 1,5 teorik garanti).
- p-Median ↔ MCLP ödünleşimi: MCLP %100 kapsamayı, ortalama mesafeyi feda ederek
  alıyor — makalede güzel bir "amaç fonksiyonu seçimi" tartışması.

## 4. Üretilen dosyalar

| Dosya | İçerik |
| :--- | :--- |
| `polis_optimizasyon.py` | Tüm pipeline (tek dosya, 9 modül) |
| `optimizasyon_haritasi.html` | İnteraktif harita: ısı haritası, mevcut/önerilen karakollar, 3 km kapsama, gerçek yolda devriye turu |
| `p_duyarlilik_analizi.png` / `p_duyarlilik_sonuclari.csv` | p ↔ hizmet kalitesi eğrileri |
| `kapsama_karsilastirmasi.png` | Mevcut vs p-Median vs MCLP kıyası |
| `dis_orneklem_dogrulama.png` | Sağlamlık testi |
| `metrik_ozet.csv` | Üç yerleşimin tüm metrikleri |
| `optimum_karakol_konumlari.csv` | Önerilen karakol koordinatları (p-median + MCLP) |
| `devriye_turu.csv` | Devriye turu sırası ve bacak mesafeleri |

## 5. Silinen dosyalar (eski projeye aitti)

`sucpy.py`, `makale.md`, `makale.tex`, `MAKALE_BILGILENDIRME.md`,
`performans_stats.png`, `cluster_quality_*`, `scalability_*`,
`statistical_*`, `londra_final_analiz.html/.png`, `__pycache__/`.
(`sucpy.py`'nin ilk commit'teki hali git geçmişinde durur: `git show ac65861:sucpy.py`)

## 6. Makale için yol haritası (kalan işler)

Kod tarafı hazır; yayına giden yolda kalan işler **yazım ve veri genişletme**:

1. **Çok aylı veri indir** (data.police.uk'den 12+ ay) → zamansal dış-örneklem
   doğrulaması otomatik devreye girer; mevsimsellik analizi eklenebilir.
2. **İkinci şehir** (örn. Chicago/NYC açık suç verisi) ile genellenebilirlik.
3. **Makaleyi İngilizce yaz**: yapı → Giriş, İlgili Çalışmalar (hotspot policing +
   facility location), Yöntem (bu dosyanın 2. bölümü), Bulgular (3. bölüm),
   Kısıtlar, Sonuç.
4. **Kısıtlar bölümünde dürüstçe belirtilecekler:** OSM `amenity=police`
   etiketinin küçük polis noktalarını da içermesi; tesis kurulum maliyeti ve
   kapasite kısıtlarının modellenmemesi; mesafelerin (yerleşim fazında) Öklid
   olması (devriye fazında gerçek yol ağı kullanılıyor); tek aylık veri.
5. **Gerçekçi hedef dergiler:** *ISPRS Int. J. of Geo-Information* (Q2),
   *Applied Sciences*, *Crime Science*; güçlü sonuçlarla *Computers, Environment
   and Urban Systems* (Q1) denenebilir. Danışman hocayla ortak yazarlık önerilir.

## 7. Çalıştırma

```bash
pip install numpy pandas scikit-learn networkx matplotlib folium osmnx pyproj pulp
python polis_optimizasyon.py all     # london | west-midlands | chicago | all
```

İnternet gerekir (OSM mevcut karakollar + yol ağı; başarısız olursa program
kuş uçuşu mesafeye düşerek devam eder).

## 8. Üç şehre genişleme (7 Temmuz 2026)

Bölüm 6'daki en kritik eksik ("tek şehir + tek ay") kapatıldı:

- **Veri:** police.uk tüm-güçler arşivinden (1,7 GB) Londra (Metropolitan +
  City of London) ve West Midlands'ın 2025-05..2026-04 aylık CSV'leri çıkarıldı;
  Chicago Data Portal SODA API'sinden aynı 12 ayın 234 bin kaydı çekildi.
  Toplam ~1,66 milyon kayıt, `data/<şehir>/` altında.
- **Kod:** `CITY_CONFIGS` ile şehir yapılandırması (sınır kutusu, EPSG
  projeksiyonu, veri şeması); Chicago suç kategorileri Birleşik Krallık önem
  ölçeğine eşlendi; çıktılar `sonuclar/<şehir>/` altına yazılıyor.
- **Zamansal doğrulama artık gerçek:** 12 aylık veride ilk 6 ay eğitim → son
  6 ay test bölmesi otomatik devreye girdi (açıklar: Londra %−0,15,
  West Midlands %1,03, Chicago %0,54 — yerleşimler zamana dayanıklı).
- **Ana bulgu üç şehirde tekrarlandı:** eşit tesis sayısında talep-ağırlıklı
  ortalama mesafe iyileşmesi Londra %28,6, Birmingham %33,8, Chicago %53,5;
  MCLP her üç şehirde %100 3-km kapsamaya ulaştı; mevcut hizmet seviyesi
  %39–73 daha az tesisle yakalanabiliyor. Yöntem şehir/ülke/veri-şeması
  bağımsız çalışıyor — "genellenebilirlik" itirazı kapandı.

Bu genişlemeyle Bölüm 6'daki yol haritasından geriye kalanlar: OSM karakol
listesinin resmi kayıtlarla çapraz doğrulanması, baseline çeşitlendirme +
ağırlık duyarlılık analizi ve İngilizce makale yazımı.
