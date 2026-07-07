# -*- coding: utf-8 -*-
"""
VERİMLİLİK SENARYOSU: p=80 (BAŞABAŞ NOKTASI)
=============================================
p duyarlılık analizinin gösterdiği başabaş noktasını ayrı bir senaryo
olarak üretir: mevcut hizmet seviyesi (OSM'deki tüm polis tesisleri,
p=148), optimal yerleşimle p=80 karakolda yakalanmaktadır (%46 daha az
tesis). Bu betik, makalenin "verimlilik senaryosu" bölümü için harita,
metrik tablosu ve karşılaştırma grafiği üretir.

Çalıştırma:  python senaryo_p80.py [şehir] [p]
Varsayılan:  london, p=80
Çıktılar:    sonuclar/<şehir>/p80/
"""

import os
import sys

import numpy as np
import pandas as pd

from polis_optimizasyon import (
    CITY_CONFIGS, CrimeDataLoader, DemandGrid, PMedianSolver, MCLPSolver,
    GRID_SIZE_M, CAND_GRID_M, RANDOM_SEED,
    set_projection, project_to_meters, unproject_to_wgs,
    evaluate_solution, fetch_existing_stations, build_map, plot_comparison,
)


def main(city='london', p_scenario=80):
    cfg = CITY_CONFIGS[city]
    set_projection(cfg.get('epsg', 27700))
    outdir = os.path.join('sonuclar', city, f'p{p_scenario}')
    os.makedirs(outdir, exist_ok=True)
    np.random.seed(RANDOM_SEED)

    print('=' * 70)
    print(f"VERİMLİLİK SENARYOSU — {cfg['name'].upper()}, p={p_scenario}")
    print('=' * 70)

    # 1) Veri ve talep modeli (ana analizle birebir aynı kurulum)
    df = CrimeDataLoader(cfg).load()
    grid = DemandGrid(df, GRID_SIZE_M)
    cand_xy = DemandGrid(df, CAND_GRID_M).xy
    print(f"[TALEP] {grid.n} talep hücresi, {len(cand_xy)} aday konum")

    # 2) Mevcut tesisler (baz çizgi)
    existing = fetch_existing_stations(cfg['bbox'])
    existing_metrics = None
    if existing is not None:
        ex_x, ex_y = project_to_meters(existing[:, 1], existing[:, 0])
        existing_metrics = evaluate_solution(
            np.column_stack([ex_x, ex_y]), grid.xy, grid.weights)
        print(f"[MEVCUT] {len(existing)} tesis, "
              f"ort. mesafe {existing_metrics['weighted_mean_km']:.3f} km")

    # 3) p-Median, p=p_scenario
    print(f"\n--- p-MEDIAN (Teitz-Bart, p={p_scenario}) ---")
    pm = PMedianSolver(grid.xy, grid.weights, cand_xy)
    sel_pm, _ = pm.teitz_bart(p_scenario)
    pmed_xy = cand_xy[sel_pm]
    pmed_metrics = evaluate_solution(pmed_xy, grid.xy, grid.weights)

    # 4) MCLP (açgözlü), p=p_scenario — kapsama perspektifi
    print(f"\n--- MCLP (açgözlü, p={p_scenario}) ---")
    mclp = MCLPSolver(grid.xy, grid.weights, cand_xy)
    sel_mclp, cov = mclp.greedy(p_scenario)
    print(f"   kapsanan ağırlık %{100 * cov / grid.weights.sum():.2f}")
    mclp_xy = cand_xy[sel_mclp]
    mclp_metrics = evaluate_solution(mclp_xy, grid.xy, grid.weights)

    # 5) Çıktılar
    lon_pm, lat_pm = unproject_to_wgs(pmed_xy[:, 0], pmed_xy[:, 1])
    lon_mc, lat_mc = unproject_to_wgs(mclp_xy[:, 0], mclp_xy[:, 1])
    pmed_latlon = np.column_stack([lat_pm, lon_pm])
    mclp_latlon = np.column_stack([lat_mc, lon_mc])

    metrics_by_method = {}
    if existing_metrics:
        metrics_by_method[f'Mevcut karakollar'] = existing_metrics
    metrics_by_method['p-Median (önerilen)'] = pmed_metrics
    metrics_by_method['MCLP (önerilen)'] = mclp_metrics

    plot_comparison(metrics_by_method,
                    out=os.path.join(outdir, 'kapsama_karsilastirmasi.png'))
    build_map(df, pmed_latlon, mclp_latlon, existing, None, None,
              out=os.path.join(outdir, 'optimizasyon_haritasi.html'))

    rows = []
    for i, (la, lo) in enumerate(pmed_latlon):
        rows.append({'method': 'p-median', 'id': i + 1, 'lat': la, 'lon': lo})
    for i, (la, lo) in enumerate(mclp_latlon):
        rows.append({'method': 'mclp', 'id': i + 1, 'lat': la, 'lon': lo})
    pd.DataFrame(rows).to_csv(
        os.path.join(outdir, 'optimum_karakol_konumlari.csv'), index=False)

    summary = []
    for name, met in metrics_by_method.items():
        r = {'method': name}
        r.update(met)
        summary.append(r)
    pd.DataFrame(summary).to_csv(
        os.path.join(outdir, 'metrik_ozet.csv'), index=False)
    print(f"[CSV] {outdir}/: optimum_karakol_konumlari.csv, metrik_ozet.csv")

    # 6) Özet
    print('\n' + '=' * 70)
    print('VERİMLİLİK SENARYOSU ÖZETİ')
    print('=' * 70)
    if existing_metrics:
        n_ex = len(existing)
        print(f"Mevcut {n_ex} tesis: ort. {existing_metrics['weighted_mean_km']:.3f} km, "
              f"3 km kapsama %{existing_metrics['coverage_3km_pct']:.1f}")
        print(f"Optimize p={p_scenario}: ort. {pmed_metrics['weighted_mean_km']:.3f} km, "
              f"3 km kapsama %{pmed_metrics['coverage_3km_pct']:.1f}")
        print(f"-> %{100 * (1 - p_scenario / n_ex):.0f} daha az tesisle "
              f"mevcut hizmet seviyesi korunuyor/aşılıyor.")


if __name__ == '__main__':
    args = sys.argv[1:]
    city = args[0] if args else 'london'
    p = int(args[1]) if len(args) > 1 else 80
    main(city, p)
