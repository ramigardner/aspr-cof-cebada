import ee, json, hashlib
from datetime import datetime, timezone

ee.Initialize(project='decoded-plane-495419-c9')

NDVI_MIN = 0.18
NDVI_MAX = 0.75
BSI_MAX  = 0.15

def verificar_lote(lat, lon, campaña="2024"):
    punto = ee.Geometry.Point([lon, lat])
    lote  = punto.buffer(500)
    año   = int(campaña)

    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterBounds(lote)
           .filterDate(f"{año}-06-01", f"{año}-09-30")
           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25)))

    n = col.size().getInfo()
    if n == 0:
        return {'estado': 'ERROR', 'msg': 'Sin imágenes disponibles'}

    img  = col.median()
    ndvi = img.normalizedDifference(['B8','B4']).rename('NDVI')
    bsi  = img.expression(
        '((SWIR+RED)-(NIR+BLUE))/((SWIR+RED)+(NIR+BLUE))',
        {'SWIR':img.select('B11'),'RED':img.select('B4'),
         'NIR':img.select('B8'),'BLUE':img.select('B2')}
    ).rename('BSI')
    ndmi = img.normalizedDifference(['B8','B11']).rename('NDMI')

    vals = (ndvi.addBands(bsi).addBands(ndmi)
            .reduceRegion(ee.Reducer.mean(), lote, 10).getInfo())

    ndvi_v = round(vals.get('NDVI',-99), 4)
    bsi_v  = round(vals.get('BSI', -99), 4)
    ndmi_v = round(vals.get('NDMI',-99), 4)

    checks = {
        'cultivo_activo': {
            'estado': 'PASS' if NDVI_MIN <= ndvi_v <= NDVI_MAX else
                      'FAIL' if ndvi_v < 0.10 else 'ALERTA',
            'valor': ndvi_v, 'umbral': f'{NDVI_MIN}-{NDVI_MAX}'
        },
        'calidad_suelo': {
            'estado': 'PASS' if bsi_v <= BSI_MAX else 'ALERTA',
            'valor': bsi_v, 'umbral': f'<{BSI_MAX}'
        },
        'estres_hidrico': {
            'estado': 'PASS' if ndmi_v >= 0 else 'ALERTA',
            'valor': ndmi_v, 'umbral': '>=0'
        }
    }

    estados = [v['estado'] for v in checks.values()]
    general = 'FAIL' if 'FAIL' in estados else \
              'ALERTA' if 'ALERTA' in estados else 'PASS'

    r = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'lat': lat, 'lon': lon, 'campaña': campaña,
        'imagenes_s2': n,
        'indices': {'NDVI': ndvi_v, 'BSI': bsi_v, 'NDMI': ndmi_v},
        'verificaciones': checks,
        'estado_general': general,
        'fuente': 'Sentinel-2 SR / GEE'
    }
    payload = json.dumps(r, sort_keys=True, ensure_ascii=False)
    r['sha256'] = hashlib.sha256(payload.encode()).hexdigest()
    return r

if __name__ == '__main__':
    r = verificar_lote(-38.376, -60.279, "2024")
    print(json.dumps(r, indent=2, ensure_ascii=False))
