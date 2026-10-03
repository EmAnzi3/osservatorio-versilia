#!/usr/bin/env python3
"""Reconcile the 2021 census with Istat 2026 boundaries (pyshp, shapely, pyproj)."""
from __future__ import annotations
import argparse, hashlib, io, json, zipfile
from pathlib import Path
import shapefile
from shapely import make_valid
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import CRS, Transformer
from acquire_a3_benchmark_istat_fragility_2022 import download

ROOT=Path(__file__).resolve().parents[1]
LAYERS={'area':'opi_a_dgrt_1155_21','line':'opi_l_dgrt_1155_21','point':'opi_pt_dgrt_1155_21'}

def reader(archive,stem,encoding):
    return shapefile.Reader(shp=io.BytesIO(archive.read(stem+'.shp')),shx=io.BytesIO(archive.read(stem+'.shx')),dbf=io.BytesIO(archive.read(stem+'.dbf')),encoding=encoding)

def acquire(works_bytes,boundary_bytes):
    frozen=json.loads((ROOT/'data/source-snapshots/bonifica-rischio-v126-gis.json').read_text())
    for body,key in [(works_bytes,'hydraulicWorks'),(boundary_bytes,'istatBoundaries')]:
        if hashlib.sha256(body).hexdigest()!=frozen['sources'][key]['sha256']: raise RuntimeError('Hydraulic official source hash mismatch')
    outer=zipfile.ZipFile(io.BytesIO(works_bytes)); works=zipfile.ZipFile(io.BytesIO(outer.read('DGRT_1155_2021_ricognizione_opere_idrauliche.zip')))
    boundaries=zipfile.ZipFile(io.BytesIO(boundary_bytes))
    codes={x['istatCode']:name for name,x in frozen['boundaries']['byTown'].items()}
    stem='Com01012026_g/Com01012026_g_WGS84'
    project=Transformer.from_crs(CRS.from_wkt(boundaries.read(stem+'.prj').decode()),3003,always_xy=True).transform
    towns={}
    for row in reader(boundaries,stem,'utf8').iterShapeRecords():
        code=str(row.record.as_dict()['PRO_COM_T'])
        if code in codes:
            if codes[code] in towns: raise RuntimeError('Hydraulic duplicate municipal boundary')
            towns[codes[code]]=transform(project,shape(row.shape.__geo_interface__))
    regions=[transform(project,shape(row.shape.__geo_interface__)) for row in reader(boundaries,'Reg01012026_g/Reg01012026_g_WGS84','utf8').iterShapeRecords() if row.record.as_dict()['COD_REG']==9]
    if len(towns)!=7 or len(regions)!=1: raise RuntimeError('Hydraulic boundary scope mismatch')
    region=regions[0]; counts={}; proof={name:{} for name in towns}; invalid=0
    for kind,stem in LAYERS.items():
        if not CRS.from_wkt(works.read(stem+'.prj').decode()).equals(CRS.from_epsg(3003)): raise RuntimeError('Hydraulic source CRS mismatch')
        geoms=[shape(s.__geo_interface__) for s in reader(works,stem,'cp1252').iterShapes()]
        if len(geoms)!=frozen['hydraulicWorks']['sourceFeatureCounts'][kind]: raise RuntimeError('Hydraulic source layer count mismatch')
        for geom in geoms:
            if geom.is_empty: raise RuntimeError('Hydraulic empty geometry')
            if not geom.is_valid:
                invalid+=1; repaired=make_valid(geom)
                # The metric counts intersections, not areas or lengths.
                if any(geom.intersects(p)!=repaired.intersects(p) for p in [region,*towns.values()]): raise RuntimeError('Hydraulic invalid geometry changes count after repair')
        count=sum(g.intersects(region) for g in geoms)
        if count!=len(geoms): raise RuntimeError('Hydraulic source features outside Tuscany: explicit handling required')
        counts[kind]=count
        for name,poly in towns.items():
            n=sum(g.intersects(poly) for g in geoms)
            if n!=frozen['hydraulicWorks']['byTown'][name][kind]['sourceFeaturesIntersecting']: raise RuntimeError('Hydraulic 7/7 per-layer reconciliation mismatch')
            proof[name][kind]=n
    municipal={frozen['boundaries']['byTown'][name]['istatCode']:{'town':name,'counts':detail,'value':sum(detail.values())} for name,detail in proof.items()}
    return {'schemaVersion':1,'publisher':'Regione Toscana — Ricognizione opere idrauliche DGRT 1155/2021','sourceProfileId':'regione-toscana-opere-idrauliche-2021','sourceUrl':frozen['sources']['hydraulicWorks']['url'],
        'sources':frozen['sources'],'raw':{'tuscany':counts},'municipalReconciliation':municipal,
        'qualityGate':{'status':'PASS','errors':[],'publicReconciliation':'7/7 exact per-layer GIS intersections','sourceHashes':'Both official archives exactly match governed snapshot','invalidSourceGeometries':invalid,'invalidGeometryCheck':'Intersection membership unchanged after make_valid for Tuscany and all seven municipalities'},
        'benchmarks':{'hydraulicWorksCensusElements':{'year':'2021','unit':'number','tuscany':sum(counts.values()),'italy':None}},
        'scope':{'note':'Feature del censimento regionale DGRT 1155/2021 che intersecano la Toscana: 82 areali, 2.572 lineari, 1.012 puntuali, contate una volta per record sorgente e layer. Esclusi i tratti del reticolo DCR 81/2021. Non è un conteggio di cantieri o strutture fisiche; Italia non disponibile nella fonte regionale.'}}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,required=True); parser.add_argument('--works-zip',type=Path); parser.add_argument('--boundaries-zip',type=Path); args=parser.parse_args()
    src=json.loads((ROOT/'data/source-snapshots/bonifica-rischio-v126-gis.json').read_text())['sources']
    works=args.works_zip.read_bytes() if args.works_zip else download(src['hydraulicWorks']['url'],'application/zip')
    boundaries=args.boundaries_zip.read_bytes() if args.boundaries_zip else download(src['istatBoundaries']['url'],'application/zip')
    snapshot=acquire(works,boundaries); args.output.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
    print('Hydraulic census candidate PASS: Tuscany 3666 source features; 7/7 per-layer reconciliation; regional intersections and exact hashes verified. Not ACQUIRED until publication gate.')

if __name__=='__main__': main()
