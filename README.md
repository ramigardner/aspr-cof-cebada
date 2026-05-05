# Certificación Soberana de Cebada Maltera Bonaerense
## Verificación Satelital Ed25519 — ASPR/COF Piloto 2026

Este repositorio contiene las herramientas y el primer certificado soberano (#001) para el proyecto de certificación de cebada maltera en la provincia de Buenos Aires (Tres Arroyos).

### Descripción
El sistema utiliza criptografía de curva elíptica (Ed25519) para firmar bloques de datos que vinculan la identidad del productor, las coordenadas del lote y la verificación satelital de la cosecha.

### Contenido
- `certificado_cebada_001.pdf`: Certificado generado para el piloto inicial.
- `bloque_firmado.json`: Datos técnicos y firma digital del certificado.
- `cof_cebada_public.pem`: Clave pública para verificar la autenticidad.
- `cof_verificador_cebada.py`: Script de Python para validar la firma de los bloques.
- `cert_pdf_generator.py`: Generador de certificados con código QR integrado.
- `qr_verification.png`: Código QR para verificación rápida.

### Uso del Verificador
Para verificar la integridad de un bloque firmado, ejecute:
```bash
python3 cof_verificador_cebada.py
```

### Licencia
Este proyecto está bajo la Licencia MIT.
