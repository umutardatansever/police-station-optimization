"""
LONDRA SUÇ ANALİZİ VE ROTA OPTİMİZASYONU (FİNAL VERSİYON - FOLIUM ENTEGRASYONLU - GÖRÜNÜRLÜK İYİLEŞTİRMESİ)
=========================================================================================================
Algoritma Analizleri Dersi - Final Projesi

GÜNCELLEMELER  Görünürlük):
2. Isı Haritası (HeatMap) Ayarları:
   - radius: 11 -> 13 (Yoğunluk bölgeleri daha belirgin)
   - blur: 15 -> 10 (Daha keskin ve net görüntü)
   - min_opacity: 0.3 eklendi (Düşük yoğunluklu alanlar daha görünür)
"""

import os
import sys
import warnings
import time
import tracemalloc
import heapq
from collections import defaultdict

# Veri ve Matematik
import numpy as np
import pandas as pd

# Algoritmalar
from sklearn.cluster import KMeans, DBSCAN
import networkx as nx

# Görselleştirme (Grafikler için)
import matplotlib.pyplot as plt

# Haritalama (Harita için)
import folium
from folium import plugins

# Gereksiz uyarıları kapat
warnings.filterwarnings('ignore')

# ---------------------------------------------------------
# 1. VERİ YÜKLEME MODÜLÜ
# ---------------------------------------------------------
class RealCrimeDataLoader:
    def __init__(self, csv_path='london_crime.csv'):
        self.csv_path = csv_path
        
    def load_data(self, max_samples=50000):
        print(f"🇬🇧 Londra gerçek suç verileri aranıyor: {self.csv_path}...")
        
        if not os.path.exists(self.csv_path):
            print(f"❌ HATA: '{self.csv_path}' dosyası bulunamadı!")
            return None

        try:
            df = pd.read_csv(self.csv_path)
            # Kritik sütunların boş olup olmadığını kontrol et
            df = df.dropna(subset=['Latitude', 'Longitude'])
            
            # Sütun isimlendirmesini standartlaştır
            df = df.rename(columns={'Latitude': 'lat', 'Longitude': 'lon', 'Crime type': 'type'})
            
            # Outlier Temizliği (Londra koordinatları dışındakileri at)
            df = df[
                (df['lat'] > 51.28) & (df['lat'] < 51.70) & 
                (df['lon'] > -0.55) & (df['lon'] < 0.35)
            ]

            if len(df) > max_samples:
                print(f"⚠️ {len(df)} kayıt arasından {max_samples} tanesi seçiliyor (Big Data)...")
                df = df.sample(n=max_samples, random_state=42)
            
            print(f"✅ Analize Hazır Veri: {len(df)} adet.")
            return df[['lat', 'lon', 'type']]
            
        except Exception as e:
            print(f"❌ Bir hata oluştu: {e}")
            return None

# ---------------------------------------------------------
# 2. KÜMELEME (CLUSTERING) ANALİZ MODÜLÜ
# ---------------------------------------------------------
class ClusteringAnalyzer:
    def __init__(self, data):
        self.data = data
        self.features = data[['lat', 'lon']].values
        
    def kmeans_clustering(self, n_clusters=5):
        print(f"\n🔵 K-Means başlatılıyor (k={n_clusters})...")
        tracemalloc.start()
        start_time = time.time()
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(self.features)
        centroids = kmeans.cluster_centers_
        
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        memory = peak / 1024 / 1024
        tracemalloc.stop()
        elapsed = end_time - start_time
        
        print(f"   ⏱️  Süre: {elapsed:.4f}s | 💾 Bellek: {memory:.2f}MB")
        return {'labels': labels, 'centroids': centroids, 'time': elapsed, 'memory': memory, 'name': 'K-Means'}
    
    def dbscan_clustering(self, eps=0.005, min_samples=15):
        print(f"🟢 DBSCAN başlatılıyor (eps={eps})...")
        tracemalloc.start()
        start_time = time.time()
        
        # n_jobs=-1 işlemcinin tüm çekirdeklerini kullanır
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
        labels = dbscan.fit_predict(self.features)
        
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        memory = peak / 1024 / 1024
        tracemalloc.stop()
        elapsed = end_time - start_time
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        print(f"   ⏱️  Süre: {elapsed:.4f}s | 💾 Bellek: {memory:.2f}MB | Cluster: {n_clusters}")
        return {'labels': labels, 'n_clusters': n_clusters, 'time': elapsed, 'memory': memory, 'name': 'DBSCAN'}

# ---------------------------------------------------------
# 3. ROTA OPTİMİZASYONU MODÜLÜ
# ---------------------------------------------------------
class RouteOptimizer:
    def __init__(self, hotspot_coords):
        self.hotspots = hotspot_coords
        self.n_nodes = len(hotspot_coords)
        self.graph = self.build_graph()
        
    def haversine_distance(self, coord1, coord2):
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371 # Dünya yarıçapı (km)
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c
    
    def build_graph(self):
        graph = defaultdict(list)
        for i in range(self.n_nodes):
            for j in range(i+1, self.n_nodes):
                dist = self.haversine_distance(self.hotspots[i], self.hotspots[j])
                # Graph çift yönlüdür (undirected)
                graph[i].append((j, dist))
                graph[j].append((i, dist))
        return graph
    
    def dijkstra(self, start_node=0):
        print(f"\n🔷 Dijkstra başlatılıyor...")
        tracemalloc.start()
        start_time = time.time()
        
        distances = {i: float('inf') for i in range(self.n_nodes)}
        distances[start_node] = 0
        pq = [(0, start_node)]
        
        while pq:
            curr_dist, u = heapq.heappop(pq)
            if curr_dist > distances[u]: continue
            
            for v, weight in self.graph[u]:
                new_dist = curr_dist + weight
                if new_dist < distances[v]:
                    distances[v] = new_dist
                    heapq.heappush(pq, (new_dist, v))
                    
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        memory = peak / 1024 / 1024
        tracemalloc.stop()
        elapsed = end_time - start_time
        
        print(f"   ⏱️  Süre: {elapsed:.6f}s | 💾 Bellek: {memory:.6f}MB")
        return {'time': elapsed, 'memory': memory, 'name': 'Dijkstra'}

    def a_star(self, start_node, target_node):
        print(f"⭐ A* (A-Star) başlatılıyor...")
        tracemalloc.start()
        start_time = time.time()
        
        g_score = {i: float('inf') for i in range(self.n_nodes)}
        g_score[start_node] = 0
        pq = [(0, start_node)]
        
        while pq:
            curr_f, current = heapq.heappop(pq)
            if current == target_node: break
            
            for neighbor, weight in self.graph[current]:
                tentative_g = g_score[current] + weight
                if tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    h_score = self.haversine_distance(self.hotspots[neighbor], self.hotspots[target_node])
                    f_score = tentative_g + h_score
                    heapq.heappush(pq, (f_score, neighbor))
                    
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        memory = peak / 1024 / 1024
        tracemalloc.stop()
        elapsed = end_time - start_time
        
        print(f"   ⏱️  Süre: {elapsed:.6f}s | 💾 Bellek: {memory:.6f}MB")
        return {'time': elapsed, 'memory': memory, 'name': 'A* (A-Star)'}

    def prim_mst(self):
        print(f"🟦 Prim's MST başlatılıyor...")
        tracemalloc.start()
        start_time = time.time()
        
        visited = set([0])
        mst_edges = []
        edges = [(weight, 0, to) for to, weight in self.graph[0]]
        heapq.heapify(edges)
        
        while edges and len(visited) < self.n_nodes:
            weight, frm, to = heapq.heappop(edges)
            if to in visited: continue
            
            visited.add(to)
            mst_edges.append((frm, to, weight))
            
            for next_node, next_weight in self.graph[to]:
                if next_node not in visited:
                    heapq.heappush(edges, (next_weight, to, next_node))
                    
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        memory = peak / 1024 / 1024
        tracemalloc.stop()
        elapsed = end_time - start_time
        
        print(f"   ⏱️  Süre: {elapsed:.6f}s | 💾 Bellek: {memory:.6f}MB")
        return mst_edges, {'time': elapsed, 'memory': memory, 'name': "Prim's MST"}

# ---------------------------------------------------------
# 4. GÖRSELLEŞTİRME MODÜLÜ (YENİ - HİBRİT YAPI & İYİLEŞTİRİLMİŞ GÖRÜNÜM)
# ---------------------------------------------------------
class Visualizer:
    @staticmethod
    def create_interactive_map(data, hotspots, mst_edges):
        """
        Folium kütüphanesi ile interaktif HTML harita üretir.
        Görünürlük parametreleri iyileştirilmiştir.
        """
        print("\n🌍 İnteraktif Harita Hazırlanıyor (Folium)...")
        
        # 1. Harita Altlığı (Dark Mode)
        # zoom_start=10 ile daha geniş bir perspektiften başla
        m = folium.Map(location=[51.5074, -0.1278], zoom_start=10, tiles='cartodbdark_matter')

        # --- KATMAN 1: SUÇ YOĞUNLUĞU (HEATMAP) ---
        print("   -> Heatmap katmanı işleniyor...")
        heat_data = data[['lat', 'lon']].values.tolist()
        # radius=13 (daha geniş), blur=10 (daha net), min_opacity=0.3 (daha görünür)
        plugins.HeatMap(heat_data, name="Suç Isı Haritası", radius=13, blur=10, min_opacity=0.3).add_to(m)

        # --- KATMAN 2: KARAKOL NOKTALARI (K-MEANS CENTROIDS) ---
        print("   -> Karakol noktaları işleniyor...")
        for i, (lat, lon) in enumerate(hotspots):
            # İkon
            folium.Marker(
                [lat, lon],
                popup=f"<b>Merkez Karakol {i+1}</b><br>Lat: {lat:.4f}<br>Lon: {lon:.4f}",
                icon=folium.Icon(color='red', icon='shield', prefix='fa')
            ).add_to(m)
            
            # Etki Alanı Çemberi (1.5 km)
            folium.Circle(
                [lat, lon],
                radius=1500,
                color='red',
                fill=True,
                fill_opacity=0.1
            ).add_to(m)

        # --- KATMAN 3: DEVRİYE ROTASI (MST - PRIM'S) ---
        print("   -> Rota optimizasyonu (MST) çiziliyor...")
        route_layer = folium.FeatureGroup(name="Optimize Rota (MST)")
        
        for u, v, w in mst_edges:
            coord1 = hotspots[u]
            coord2 = hotspots[v]
            
            folium.PolyLine(
                locations=[coord1, coord2],
                color='#00ffff', # Cyan neon
                weight=3,
                opacity=0.8,
                tooltip=f"Mesafe: {w:.2f} km"
            ).add_to(route_layer)
            
        route_layer.add_to(m)

        # Katman Kontrolü Ekle
        folium.LayerControl().add_to(m)

        # Kaydet
        output_file = "londra_final_analiz.html"
        m.save(output_file)
        print(f"✅ Harita başarıyla kaydedildi: {output_file}")

    @staticmethod
    def plot_performance_stats(perf_data):
        """
        Performans istatistiklerini Matplotlib ile PNG olarak kaydeder.
        """
        print("📊 Performans grafikleri hazırlanıyor...")
        
        # Dark Style Ayarları
        plt.style.use('dark_background')
        plt.rcParams.update({
            'axes.facecolor': '#050505', 
            'figure.facecolor': '#000000',
            'text.color': '#ffffff',
            'font.family': 'monospace'
        })

        names = [p['name'] for p in perf_data]
        times = [p['time'] for p in perf_data]
        mems = [p['memory'] for p in perf_data]
        colors = ['#00ffff', '#ff00ff', '#ffff00', '#00ff00', '#ff0000']

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f"ALGORİTMA PERFORMANS RAPORU", fontsize=16, fontweight='bold', color='white')

        # Grafik 1: Süre
        bars1 = axes[0].bar(names, times, color=colors, alpha=0.8, edgecolor='white')
        axes[0].set_title('İŞLEM SÜRESİ (Saniye)', fontsize=12, color='#00ffff')
        axes[0].grid(axis='y', alpha=0.2)
        for bar in bars1:
            axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                         f'{bar.get_height():.4f}s', ha='center', va='bottom', color='white', fontsize=9)

        # Grafik 2: Bellek
        bars2 = axes[1].bar(names, mems, color=colors, alpha=0.8, edgecolor='white')
        axes[1].set_title('BELLEK KULLANIMI (MB)', fontsize=12, color='#ff00ff')
        axes[1].grid(axis='y', alpha=0.2)
        for bar in bars2:
            axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                         f'{bar.get_height():.2f}MB', ha='center', va='bottom', color='white', fontsize=9)

        plt.tight_layout()
        plt.savefig('performans_stats.png', dpi=300)
        print("✅ İstatistikler kaydedildi: performans_stats.png")

# ---------------------------------------------------------
# ANA PROGRAM
# ---------------------------------------------------------
def main():
    print("="*60)
    print("LONDRA SUÇ ANALİZİ - INTERACTIVE FINAL (FOLIUM)")
    print("="*60)
    
    # 1. Veri Yükle
    loader = RealCrimeDataLoader(csv_path='london_crime.csv')
    data = loader.load_data(max_samples=50000) 
    if data is None: return

    performance_metrics = []

    # 2. Algoritmaları Çalıştır
    print("\n--- FAZ 1: KÜMELEME ---")
    analyzer = ClusteringAnalyzer(data)
    kmeans_res = analyzer.kmeans_clustering(n_clusters=15)
    performance_metrics.append(kmeans_res)
    
    # DBSCAN
    dbscan_res = analyzer.dbscan_clustering(eps=0.005, min_samples=15)
    performance_metrics.append(dbscan_res)
    
    print("\n--- FAZ 2: ROTA OPTİMİZASYONU ---")
    hotspot_coords = [(c[0], c[1]) for c in kmeans_res['centroids']]
    optimizer = RouteOptimizer(hotspot_coords)
    
    dijkstra_res = optimizer.dijkstra(start_node=0)
    performance_metrics.append(dijkstra_res)
    
    a_star_res = optimizer.a_star(start_node=0, target_node=4)
    performance_metrics.append(a_star_res)
    
    mst_edges, prim_res = optimizer.prim_mst()
    performance_metrics.append(prim_res)
    
    print("\n--- FAZ 3: GÖRSELLEŞTİRME ---")
    vis = Visualizer()
    
    # A) İNTERAKTİF HARİTA (HTML)
    vis.create_interactive_map(data, hotspot_coords, mst_edges)
    
    # B) PERFORMANS İSTATİSTİKLERİ (PNG)
    vis.plot_performance_stats(performance_metrics)
    
    print("\n✅ TÜM İŞLEMLER TAMAMLANDI.")
    print("   1. Haritayı görmek için klasördeki 'londra_final_analiz.html' dosyasına çift tıkla.")
    print("   2. İstatistikleri görmek için 'performans_stats.png' resmine bak.")

if __name__ == "__main__":
    main()