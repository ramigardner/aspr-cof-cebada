import sys
import os

# Añadir el directorio raíz al path para importar los módulos existentes
sys.path.append(os.path.abspath("/home/ramiguevara"))

from flask import Flask, request, send_file, render_template_string
from aspr_cebada.cof_verificador_cebada import verificar_lote
from aspr_cebada.cert_pdf_generator import generate_pdf
import json
import hashlib
import base64
from datetime import datetime, timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

app = Flask(__name__)

# Load real keys
PRIVATE_KEY_PATH = "/home/ramiguevara/aspr_cebada/cof_cebada_private.pem"
PUBLIC_KEY_PATH = "/home/ramiguevara/aspr_cebada/cof_cebada_public.pem"

with open(PRIVATE_KEY_PATH, 'rb') as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

with open(PUBLIC_KEY_PATH, 'rb') as f:
    public_key_pem = f.read().decode()

# Real fingerprint
fingerprint = hashlib.sha256(public_key_pem.encode()).hexdigest()

# Cargar el HTML desde el archivo para servirlo
with open("/home/ramiguevara/aspr_mobile/index.html", "r") as f:
    INDEX_HTML = f.read()

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/verificar', methods=['POST'])
def verificar():
    data = request.json
    lat = float(data.get('lat'))
    lon = float(data.get('lon'))

    # 1. Ejecutar análisis satelital real vía GEE
    try:
        resultado = verificar_lote(lat, lon)
    except Exception as e:
        return {"error": str(e)}, 500

    # 2. Firma real y guardar bloque_firmado.json
    bloque_data = {
        "partido": "TRES ARROYOS",
        "lat": lat,
        "lon": lon,
        "campana": "2024",
        "cultivo": "CEBADA",
        "emisor": "ASPR-COF",
        "certificacion_tipo": resultado.get('certificacion_tipo', 'Agricultura Regenerativa — Cebada Maltera Bonaerense'),
        "valor_mercado": resultado.get('valor_mercado', []),
        "indices": resultado['indices'],
        "verificaciones": {
            "rotacion_verificada": resultado['verificaciones'].get('rotacion_verificada', {}).get('estado', 'N/A'),
            "calidad_suelo": resultado['verificaciones']['calidad_suelo']['estado'],
            "estres_hidrico": resultado['verificaciones']['estres_hidrico']['estado']
        },
        "timestamp_utc": resultado['timestamp_utc']
    }

    # Real signature
    payload = json.dumps(bloque_data, sort_keys=True, ensure_ascii=False).encode()
    sha256 = hashlib.sha256(payload).hexdigest()
    firma_bytes = private_key.sign(payload)
    firma_b64 = base64.b64encode(firma_bytes).decode()

    bloque_firmado = {
        "bloque": bloque_data,
        "hash_sha256": sha256,
        "signature_ed25519": firma_b64,
        "public_key_fingerprint": fingerprint,
        "public_key_pem": public_key_pem
    }

    with open("/home/ramiguevara/aspr_cebada/bloque_firmado.json", "w") as f:
        json.dump(bloque_firmado, f, indent=2, ensure_ascii=False)

    # 3. Generar PDF
    generate_pdf()

    # 4. Enviar el PDF de vuelta al móvil
    pdf_path = "/home/ramiguevara/aspr_cebada/certificado_cebada_001.pdf"
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    # Ejecutar en el puerto 8080 para Cloud Shell
    app.run(host='0.0.0.0', port=8080)
