# Londra Suc Analizi ve Devriye Rotası Optimizasyonu Projesi
## Algoritma Analizi Dersi Final Projesi

Bu proje, Londra sehrine ait gercek suc verilerini yukleyerek makine ogrenmesi ve graf teorisi tabanlı yaklasımlarla analiz eder. Projenin ana amacı, suc yogunlugunun yuksek oldugu bolgeleri (sıcak noktalar / hot-spots) tespit etmek, bu noktalara yerlestirilecek merkez karakollar icin en uygun konumları belirlemek ve bu istasyonlar arasında optimize edilmis polis devriye rotaları ile minimum maliyetli yayılım agları (MST) olusturmaktır. Proje kapsamında kullanılan tum algoritmaların zaman ve bellek karmasıklıgı performansları deneysel olarak olculmekte ve analiz edilmektedir.

---

## Proje Hedefleri

1. **Yogunluk ve Kumeleme Analizi:** Londra sınırları icindeki buyuk boyutlu suc verilerini kumeleyerek dogal suc odak noktalarını (merkezleri) saptamak ve veri yogunlugunu analiz etmek.
2. **Rota Optimizasyonu:** Belirlenen suc odak noktaları arasında dolasacak ekipler icin en kısa yolları hesaplamak ve tum merkezleri birbirine baglayan en dusuk maliyetli devriye agını (Minimum Spanning Tree) kurmak.
3. **Deneysel Algoritmik Karşılaştırma:** K-Means, DBSCAN, Dijkstra, A* ve Prim's MST algoritmalarının yurutum surelerini (time) ve pik bellek tuketimlerini (memory) deneysel olarak gozlemlemek ve teorik karmasıklık analizleriyle kıyaslamak.
4. **Zengin ve İnteraktif Gorsellestirme:** Coğrafi analizleri interaktif bir harita uzerinde katmanlar halinde sunmak ve performans analizlerini profesyonel grafiklerle raporlamak.

---

## Algoritma Mimarisi ve Teorik Karmasıklık Analizi

Proje kapsamında uygulanan algoritmaların kullanım amacları, teorik zaman ve alan karmasıklıkları asagıdaki tabloda detaylandırılmıstır:

| Algoritma | Kullanım Amacı | Zaman Karmasıklıgı (Time Complexity) | Alan Karmasıklıgı (Space Complexity) |
| :--- | :--- | :--- | :--- |
| **K-Means** | Suc odak noktalarının (karakol koordinatlarının) saptanması | O(n * k * i * d) | O(n * d) |
| **DBSCAN** | Yogunluk tabanlı kumeleme ve gurultu verilerin ayıklanması | O(n * log n) ila O(n^2) | O(n) |
| **Dijkstra** | Baslangıc karakolundan diger tum noktalara en kısa yolların bulunması | O((V + E) * log V) | O(V + E) |
| **A\* (A-Star)** | Belirli iki karakol arasında sezgisel en kısa yol hesabı | O(E * log V) (Kotu senaryoda) | O(V) |
| **Prim's MST** | Tum karakolları baglayan optimum devriye agının tasarımı | O(E * log V) | O(V + E) |

### Degisken Tanımları
* **n:** Toplam suc veri noktası sayısı (Varsayılan limit: 50.000 veri satırı).
* **k:** K-Means icin hedeflenen kume sayısı (Projede k = 15 olarak set edilmistir).
* **i:** Algoritmanın yakınsama icin yaptıgı maksimum iterasyon sayısı.
* **d:** Boyut sayısı (Cografi enlem ve boylam analizi yapıldıgı icin d = 2).
* **V:** Graf uzerindeki dugum (vertex) sayısı (K-Means sonucunda olusan k = 15 merkez istasyon).
* **E:** Karakollar arasındaki baglantı yolları (Graf tam baglantılı - complete graph - oldugundan E = V * (V - 1) / 2).

---

## Veri Yukleme ve Onișleme Modulu

Veri yuku `RealCrimeDataLoader` sınıfı vasıtasıyla gercek zamanlı olarak `london_crime.csv` dosyasından okunur. Veri seti uzerinde asagıdaki onislemler yurutulur:
* **Eksik Veri Temizligi:** Enlem (Latitude) ve boylam (Longitude) bilgisi eksik olan satırlar tespit edilerek veri setinden cıkarılır.
* **Standartlastırma:** Sutun isimleri cografi kutuphanelerle uyumlu olması acısından `lat`, `lon` ve `type` (suc turu) olarak yeniden adlandırılır.
* **Cografi Filtreleme (Outlier Detection):** Londra sınırları dısındaki koordinat hatalarını ayıklamak amacıyla sadece `51.28 < lat < 51.70` enlemleri ile `-0.55 < lon < 0.35` boylamları arasındaki veriler kabul edilir.
* **Buyuk Veri Orneklemesi (Sampling):** Coğrafi veri yukunsuz calısmak ve analizi optimize etmek adına yuklenen buyuk veri setinden rastgele 50.000 kayıt secilir.

---

## Moduller ve Islevsel Detaylar

### 1. Kumeleme Analiz Modulu (ClusteringAnalyzer)
* **K-Means:** Verilen konum verilerini belirlenen kume sayısı kadar bolgeye ayırır. Elde edilen kume merkezleri (centroids), kurulması gereken polis karakolları veya devriye merkezleri olarak kabul edilir.
* **DBSCAN:** Yogunluk tabanlı calısarak yakın konumdaki suc olaylarını kume haline getirir. Gurultu (noise) parametresi sayesinde izole kalmıs tekil suc olaylarını ayırt eder. Cografi yogunluk yarıcapı `eps = 0.005` ve minimum komsu eleman sayısı `min_samples = 15` olarak yapılandırılmıstır.

### 2. Rota Optimizasyon Modulu (RouteOptimizer)
* **Mesafe Metrigi:** Dunya yuzeyindeki egriligi hesaba katan Haversine formulu kullanılarak karakol koordinatları arasındaki gercek kusucusu mesafe (kilometre cinsinden) hesaplanır.
* **Graf Kurulumu:** Belirlenen karakol dugumleri arasında tam baglantılı (complete graph), kenar agırlıkları Haversine mesafeleri olan yonsuz bir graf insa edilir.
* **Dijkstra Algoritması:** Min-Heap (oncelik kuyrugu) veri yapısı kullanılarak belirlenen baslangıc karakolundan diger tum istasyonlara giden en kısa yolları ve toplam yol maliyetlerini hesaplar.
* **A\* (A-Star) Algoritması:** Hedef tabanlı en kısa yol analizi yapar. Algoritmanın sezgisel (heuristic) fonksiyonu olarak dugumler arasındaki Haversine cografi mesafesi kullanılmıstır. Bu sezgisel fonksiyon gercek mesafeden asla buyuk olamayacagı icin kabul edilebilir (admissible) ve tutarlıdır (consistent).
* **Prim Algoritması (MST):** Tum istasyonları en az bir hatla birbirine baglayan, hicbir dongu icermeyen ve toplam yol uzunlugu minimum olan agacı (Minimum Spanning Tree) uretir. Bu agac, bolge genelindeki en tasarruflu devriye devresini simgeler.

### 3. Gorsellestirme ve Raporlama Modulu (Visualizer)
* **İnteraktif Harita (londra_final_analiz.html):** Folium kutuphanesi kullanılarak Dark Mode (cartodbdark_matter) stilinde interaktif bir harita uretilir. Harita asagıdaki katmanlardan olusur ve bu katmanlar sag ustteki panelden acılıp kapatılabilir:
  * *Suc Isı Haritası (HeatMap):* Suc olaylarının yogunlastıgı alanları gosterir (`radius = 13`, `blur = 10`, `min_opacity = 0.3`).
  * *Karakol Noktaları:* K-Means ile belirlenen 15 adet merkez karakol kalkan simgesiyle haritada konumlandırılır. Ayrıca her karakolun etrafına 1.5 kilometrelik kapsama alanını temsil eden dairesel bolgeler cizilir.
  * *Optimum Devriye Rotası (MST):* Prim's MST tarafından uretilen agac baglantıları neon turkuaz (`#00ffff`) cizgilerle haritada gosterilir. Her bir cizginin uzerine gelindiginde iki karakol arasındaki Haversine mesafesi tooltip olarak gosterilir.
* **Performans Raporu Grafikleme (performans_stats.png):** Matplotlib kutuphanesi kullanılarak karanlık tema arka planında iki ayrı grafik cizdirilir:
  * Algoritmaların milisaniye hassasiyetindeki islem yurutum sureleri.
  * Algoritmaların pik seviyedeki bellek kullanımları (Megabayt cinsinden).

---

## Proje Dizin Yapısı

* **sucpy.py:** Projenin veri yukleme, kumeleme, rota hesaplama ve gorsellestirme adımlarını yoneten tekil Python kaynak kod dosyası.
* **london_crime.csv:** Londra genelindeki gercek suc olaylarının koordinatlarını ve kategorilerini iceren ana veri seti.
* **londra_final_analiz.html:** Uretilen interaktif Folium coğrafi analiz haritası.
* **performans_stats.png:** Deneysel bellek ve zaman performans raporunu barındıran grafik dosyası.

---

## Kurulum ve Sistem Gereksinimleri

Programın sorunsuz calısması icin sisteminizde Python 3.8+ surumunun ve asagıdaki kütüphanelerin yuklu olması gerekmektedir.

Gerekli paketleri yuklemek icin terminal uzerinden asagıdaki komutu calıstırabilirsiniz:

```bash
pip install numpy pandas scikit-learn networkx matplotlib folium
```

---

## Kullanım Kılavuzu

Analiz sureclerini baslatmak, haritayı ve performans grafiklerini uretmek icin proje dizinindeyken terminalden su komutu calıstırın:

```bash
python sucpy.py
```

Uygulama calıstırıldıgında su adımlar sırasıyla gerceklesecektir:
1. `london_crime.csv` dosyası aranır ve yuklenir.
2. 50.000 satırlık veriye K-Means ve DBSCAN kumeleme algoritmaları uygulanır.
3. K-Means merkezleri uzerinde Dijkstra, A* ve Prim's MST algoritmaları ile rota analizleri yurutulur.
4. Elde edilen sonuclarla `londra_final_analiz.html` interaktif haritası ve `performans_stats.png` performans grafigi olusturularak dizine kaydedilir.
5. Algoritmaların deneysel calısma sureleri ile bellek tuketim metrikleri terminal ekranına yazdırılır.

---

## Deneysel Bulgular ve Performans Raporlama Metotları

Projede algoritmik yurutum surelerinin dogru hesaplanması amacıyla yuksek cozunurluklu `time.time()` olcumleri kullanılmıstır. Bellek analizi icin Python standart kutuphanesinde yer alan ve yurutum sırasındaki pik bellek tahsisatını (peak memory allocation) donen `tracemalloc` modulunden yararlanılmıstır. 

* Kumeleme fazında, K-Means veri seti genelinde kararlı merkezler uretirken, DBSCAN yogunluk sınırlarına gore gurultuleri basarıyla ayıklamaktadır.
* Rota optimizasyonu fazında, Prim's MST algoritması tum istasyonları birbirine baglayan en ekonomik ag baglantısını kurarak Dijkstra rotalarının toplamına kıyasla daha verimli bir toplam yol uzunlugu saglamaktadır.
* A* arama algoritması, Haversine sezgisel fonksiyonunu kullanarak hedef odaklı yol bulma islemlerinde Dijkstra'ya gore daha odaklı bir dugum taraması yapmaktadır.

---

## Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Detaylar için LICENSE dosyasına bakabilirsiniz.

