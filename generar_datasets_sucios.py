"""
Generador de datasets sucios para la Ruta Pandas.

Cada archivo simula un problema REAL de la vida laboral:
  - Un ERP que exporta ';' y decimal ','
  - Un CRM con duplicados y texto en 6 alfabetos distintos
  - Un maestro de productos con acentos, unidades y sufijos societarios
  - Una API de paqueteria con 3 husos horarios y estados en texto libre
  - Un extracto bancario con formatos monetarios mezclados
  - Una encuesta con Likert como texto y HTML sin limpiar

Todo es DETERMINISTA: misma semilla -> mismos datos. Linux / macOS / Windows.

Uso:
    python generar_datasets_sucios.py
    python generar_datasets_sucios.py --out datos --seed 42
"""

from __future__ import annotations

import argparse
import random
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RNG = random.Random(42)
NPRNG = np.random.default_rng(42)


def _d(min_: int, max_: int) -> int:
    """Dias aleatorios como int nativo de Python (timedelta no acepta np.int64)."""
    return int(NPRNG.integers(min_, max_))


def _f(min_: float, max_: float) -> float:
    return float(NPRNG.uniform(min_, max_))


def _pick(seq, n: int = 1):
    return RNG.choices(seq, k=n)


def _slug(nombre: str) -> str:
    s = unicodedata.normalize("NFKD", nombre)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower().replace(" ", "")
    s = "".join(c if (c.isalnum() or c in ".-_") else "" for c in s)
    return s[:28] or "sin"


def _fecha_erp(d: datetime) -> str:
    """dd/mm/yyyy, como lo exporta un ERP en formato europeo."""
    return d.strftime("%d/%m/%Y")


def _escalar(v: float) -> str:
    """float -> texto con coma decimal, sin separador de miles."""
    return f"{v:.2f}".replace(".", ",")


def _europeo(v: float) -> str:
    """float -> '1.234,56', con signo. El punto de miles sale si |v| >= 1000."""
    sign = "-" if v < 0 else ""
    texto = f"{abs(v):,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return sign + texto


def _offset_madrid(d: datetime) -> int:
    """Horas que hay que restar a la hora local de Madrid para obtener UTC.

    En 2024 el cambio de primavera es el 31 de marzo a las 02:00 (el reloj
    salta a las 03:00, UTC+1 -> UTC+2) y el de otoño el 27 de octubre a las
    03:00 (el reloj vuelve a las 02:00, UTC+2 -> UTC+1). La hora 02:00-03:00
    del 27 de octubre existe dos veces; aquí se toma como horario de verano.
    """
    primavera = datetime(2024, 3, 31, 2, 0, 0)
    otono = datetime(2024, 10, 27, 3, 0, 0)
    if primavera <= d < otono:
        return 2
    return 1


def _offset_horas(tz: str, d: datetime) -> int:
    if tz == "Europe/Istanbul":
        return 3  # Turquía no cambia la hora desde 2016
    if tz == "Asia/Dubai":
        return 4
    return _offset_madrid(d)


def _evitar_hueco_dst(tz: str, d: datetime) -> datetime:
    """El 31 de marzo de 2024, 02:00-03:00 no existe en Madrid."""
    if tz != "Europe/Madrid":
        return d
    hueco_ini = datetime(2024, 3, 31, 2, 0, 0)
    hueco_fin = datetime(2024, 3, 31, 3, 0, 0)
    if hueco_ini <= d < hueco_fin:
        return d + timedelta(hours=1)
    return d


# ---------------------------------------------------------------------------
# 1. VENTAS ESTE: export de ERP con ';' y decimal ','
# ---------------------------------------------------------------------------

REGIONES = ["Norte", "Centro", "Sur", "Este", "Oeste", "Canarias", "Baleares"]
CATEGORIAS = [
    "Electrónica", "Hogar", "Moda", "Alimentación",
    "Farmacia", "Automóvil", "Jardinería", "Juguetes",
]
CANALES = ["Tienda física", "Web", "App móvil", "Teléfono", "Marketplace"]
METODOS_PAGO = ["Tarjeta", "PayPal", "Bizum", "Transferencia", "Contado"]


def ventas_este(n: int = 12000) -> pd.DataFrame:
    hoy = datetime(2024, 12, 31)
    filas = []
    for i in range(n):
        d = hoy - timedelta(days=_d(0, 365))
        filas.append({
            "ID Pedido": f"PED-{2024000 + i}",
            "Fecha Pedido": _fecha_erp(d),
            "ID Cliente": f"CLI-{int(NPRNG.integers(1, 3200)):05d}",
            "Region": RNG.choice(REGIONES),
            "Categoria": RNG.choice(CATEGORIAS),
            "Canal": RNG.choice(CANALES),
            "Metodo Pago": RNG.choice(METODOS_PAGO),
            "Unidades": int(NPRNG.integers(1, 12)),
            "Precio Unitario": _escalar(_f(2, 900)),
        })
    df = pd.DataFrame(filas)
    pu = df["Precio Unitario"].str.replace(",", ".", regex=False).astype(float)
    df["Importe"] = (pu * df["Unidades"]).round(2).map(_escalar)
    vacio = NPRNG.random(n) < 0.05
    descuentos = ["0", "0", "5", "10", "15", "20"]
    df["Descuento %"] = ""
    df.loc[~vacio, "Descuento %"] = NPRNG.choice(
        descuentos, size=int((~vacio).sum())
    ).astype(str)
    return df


# ---------------------------------------------------------------------------
# 2. VENTAS OESTE: mismo ERP, otra region -> TSV, ISO, punto decimal
# ---------------------------------------------------------------------------

def ventas_oeste(n: int = 9000) -> pd.DataFrame:
    hoy = datetime(2024, 12, 31)
    filas = []
    for i in range(n):
        d = hoy - timedelta(days=_d(0, 180))
        filas.append({
            "order_id": f"ORD-{i:06d}",
            "order_date": d.strftime("%Y-%m-%d"),
            "customer_id": f"CUS{int(NPRNG.integers(1, 2000)):04d}",
            "region": RNG.choice(["Oeste1", "Oeste2", "Norte1"]),
            "category": RNG.choice(CATEGORIAS),
            "qty": int(NPRNG.integers(1, 8)),
            "unit_price": f"{_f(5, 300):.2f}",
            "currency": "EUR",
        })
    df = pd.DataFrame(filas)
    df["total"] = (df["unit_price"].astype(float) * df["qty"]).round(2)
    return df


# ---------------------------------------------------------------------------
# 3. CLIENTES CRM: multi-alfabeto + duplicados + variantes de escritura
# ---------------------------------------------------------------------------

NOMBRES = {
    "ES": ["José", "María", "Antonio", "Lucía", "Manuel", "Sofía", "Javier", "Elena",
           "Begoña", "Núñez", "Peña", "Nuria", "Iván"],
    "TR": ["Mehmet", "Şule", "Çağatay", "İbrahim", "Ayşe", "Gülsüm", "Ömer", "Ünal",
           "Ğökhan", "Ibrahim", "İpek", "Yılmaz", "Demir", "Şahin", "Öztürk", "Çelik",
           "Güneş", "Kaya", "Çavuş", "Doğan", "Şirin", "Özlem"],
    "AE": ["محمد", "فاطمة", "أحمد", "عائشة", "خالد", "نورة", "سارة", "عبدالله",
           "ليلى", "يوسف", "مريم", "حسن"],
    "DE": ["Hans", "Greta", "Jürgen", "Käthe", "Björn", "Søren", "Ægir",
           "Müller", "Schröder", "Weiß", "Groß", "Bär", "Löwe", "Käufer"],
    "SE": ["Åsa", "Björn", "Sören", "Ingmar", "Örjan", "Måns", "Söderberg", "Ångström"],
    "PL": ["Łukasz", "Krzysztof", "Agnieszka", "Wojciech", "Żaneta", "Miłosz",
           "Grzegorz", "Świątek", "Ćwikła", "Sędzik", "Łukasiewicz"],
}

APELLIDOS = {
    "ES": ["García", "Rodríguez", "González", "Fernández", "López", "Martínez",
           "Sánchez", "Pérez", "Gómez", "Muñoz"],
    "TR": ["Yılmaz", "Demir", "Şahin", "Öztürk", "Çelik", "Güneş", "Kaya",
           "Çavuş", "Doğan", "Şirin", "Özlem"],
    "AE": ["الحسن", "العلي", "المنصوري", "السويدي", "خليل", "النجار", "الشامسي", "النعيمي"],
    "DE": ["Müller", "Schmidt", "Weiß", "Schröder", "Käufer", "Groß", "Bär", "Löwe"],
    "SE": ["Andersson", "Söderberg", "Ångström", "Öberg", "Lövgren", "Björnsson"],
    "PL": ["Kowalski", "Żółkiewski", "Ćwikła", "Świątek", "Łukasiewicz", "Sędzik"],
}

CASOS_ESPECIALES = [
    "Ibrahim",    # 'I' -> 'ı' (i sin punto) al aplicar lower()
    "İbrahim",    # 'İ' -> 'i' + punto combinante: 1 caracter -> 2
    "istanbul",   # 'I' minuscula -> 'i' (no es 'ı')
    "IĞDIR",      # I + G breve
    "Mueller",    # transliterado
    "Müller",     # original
    "Straße",     # ß -> ss
    "STRASSE",
    "Soderberg",  # sin diacritico
    "Söderberg",  # con diacritico
    "AEON",       # ligadura
    "Muḥammad",   # latín con punto suscrito, no es tashkil
    "محمد",       # árabe sin tashkil
    "أَحْمَد",    # árabe con tashkil (las vocales cuentan en len)
    "Al-Farsi",
    "Ahmad",      # transliterado
    "أحمد",
    "Łukasz",     # L con barra
    "Lukasz",
    "Jürgen",     # u con umlaut
    "Jurgen",
    "Çağlayan",
    "Caglayan",
    "Đorđe",
    "Dorđe",
]

CIUDADES = {
    "ES": ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Málaga"],
    "TR": ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya"],
    "AE": ["Dubai", "Abu Dhabi", "Sharjah", "Al Ain"],
    "DE": ["Berlin", "Hamburg", "München", "Köln", "Düsseldorf"],
    "SE": ["Estocolmo", "Göteborg", "Malmö", "Uppsala"],
    "PL": ["Varsovia", "Cracovia", "Gdansk", "Wroclaw", "Poznań"],
}


def clientes_crm(n_base: int = 6000) -> pd.DataFrame:
    paises = list(NOMBRES.keys())
    pesos = [40, 20, 12, 12, 8, 8]
    filas = []
    for i in range(n_base):
        pais = RNG.choices(paises, weights=pesos)[0]
        nombre = f"{RNG.choice(NOMBRES[pais])} {RNG.choice(APELLIDOS[pais])}"
        filas.append({
            "cliente_id": f"C-{i:05d}",
            "nombre": nombre,
            "pais": pais,
            # El id va en el email: dos personas con el mismo nombre no comparten
            # buzón. Las variantes de escritura copian esta fila y conservan el email.
            "email": f"{_slug(nombre)}.{i}@empresa.com",
            "telefono": f"+{int(NPRNG.integers(34, 972))} {int(NPRNG.integers(600, 999))}{int(NPRNG.integers(100, 999))}{int(NPRNG.integers(100, 999))}",
            "alta": _fecha_erp(datetime(2021, 1, 1) + timedelta(days=_d(0, 1400))),
            "segmento": RNG.choice(["A", "B", "C", "D"]),
            "ciudad": RNG.choice(CIUDADES[pais]),
            "saldo": _escalar(_f(-2000, 12000)),
        })
    df = pd.DataFrame(filas)

    # --- Variantes de escritura del MISMO cliente (caso didactico central) ---
    idx = df.sample(n=int(len(df) * 0.35), random_state=1).index
    variantes = []
    for _, row in df.loc[idx].iterrows():
        v = row["nombre"]
        r = RNG.random()
        if r < 0.30:
            v = v.upper()
        elif r < 0.55:
            v = v.lower()
        if RNG.random() < 0.40:
            v = "".join(
                c for c in unicodedata.normalize("NFD", v)
                if unicodedata.category(c) != "Mn"
            )
        if RNG.random() < 0.30:
            v = v.replace("ß", "ss").replace("ø", "o").replace("Ø", "O").replace("ł", "l")
        if RNG.random() < 0.20 and " " in v:
            # Espacio raro, no borrado: la clave canónica lo colapsa.
            # Borrar el espacio partiría al mismo cliente_id en dos claves.
            v = v.replace(" ", "\u00a0", 1)
        nuevo = row.copy()
        nuevo["nombre"] = v
        # El email no cambia: es la señal estable de "es la misma persona".
        nuevo["saldo"] = _escalar(float(row["saldo"].replace(",", ".")) * _f(0.9, 1.1))
        variantes.append(nuevo)
    df = pd.concat([df, pd.DataFrame(variantes)], ignore_index=True)

    # --- Casos especiales explicitos (leccion de alfabetos) ---
    pais_caso = {
        "Ibrahim": "TR", "İbrahim": "TR", "istanbul": "TR", "IĞDIR": "TR",
        "Çağlayan": "TR", "Caglayan": "TR",
        "Mueller": "DE", "Müller": "DE", "Straße": "DE", "STRASSE": "DE",
        "Jürgen": "DE", "Jurgen": "DE",
        "Soderberg": "SE", "Söderberg": "SE",
        "Łukasz": "PL", "Lukasz": "PL",
        "Đorđe": "ES", "Dorđe": "ES", "AEON": "ES",
        "Muḥammad": "AE", "محمد": "AE", "أَحْمَد": "AE", "أحمد": "AE",
        "Ahmad": "AE", "Al-Farsi": "AE",
    }
    extra = []
    for nombre in CASOS_ESPECIALES:
        for k in range(RNG.randint(3, 9)):
            pais = pais_caso[nombre]
            extra.append({
                "cliente_id": f"C-SPEC-{len(extra):04d}",
                "nombre": nombre,
                "pais": pais,
                "email": f"{_slug(nombre)}.{len(extra)}@caso.especial",
                "telefono": f"+34 600{len(extra):06d}",
                "alta": _fecha_erp(datetime(2022, 1, 1) + timedelta(days=_d(0, 900))),
                "segmento": RNG.choice(["A", "B", "C", "D"]),
                "ciudad": RNG.choice(CIUDADES.get(pais, CIUDADES["ES"])),
                "saldo": _escalar(_f(0, 5000)),
            })
    df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)

    # --- 3% de teléfonos vacíos, antes de copiar filas ---
    vacios_tel = df.sample(frac=0.03, random_state=9).index
    df.loc[vacios_tel, "telefono"] = ""

    # --- Espacios dobles y tabuladores. Van ANTES de la copia exacta:
    #     si se aplican después, la copia deja de ser exacta.
    sucio = df.sample(n=int(len(df) * 0.10), random_state=3).index
    df.loc[sucio, "nombre"] = (
        df.loc[sucio, "nombre"]
        .str.strip()
        .str.replace(r"\s+", "  ", regex=True)
    )
    sucio2 = df.sample(n=int(len(df) * 0.03), random_state=5).index
    df.loc[sucio2, "nombre"] = (
        df.loc[sucio2, "nombre"].map(lambda v: "\t" + str(v))
    )

    # --- 400 filas duplicadas EXACTAS (el mismo registro importado dos veces) ---
    df = pd.concat([df, df.sample(n=400, random_state=7)], ignore_index=True)

    return df.iloc[NPRNG.permutation(len(df))].reset_index(drop=True)


# ---------------------------------------------------------------------------
# 4. PRODUCTOS: maestro con acentos, unidades, sufijos societarios
# ---------------------------------------------------------------------------

BASE_PRODUCTOS = [
    "Sartén", "Sarten", "Cafetera", "Cafetera Expresso", "Cafetera Expreso",
    "Teléfono Móvil", "Telefono Movil", "AURICULARES INALÁMBRICOS", "Auriculares inalambricos",
    "Müller Mix 500g", "Mueller Mix 500 g", "MÜLLER MIX 500G",
    "Jamón Ibérico", "Jamon Iberico", "Jamon iberico curado",
    "Söderberg Käse", "Soderberg Kase", "SODERBERG KÄSE",
    "Zapatillas Running", "Zapatillas Running Negro", "ZAPATILLAS RUNNING",
    "Bicicleta Ciudad", "Bicicleta de Ciudad", "BICI MONTAÑA",
    "Pañal Premium Talla 3", "Panial Premium Talla 3",
    "Café Molido 250g", "Cafe Molido 250 g", "CAFÉ MOLIDO 250G",
    "Søndergaard Thon 200g", "Sondergaard Thon 200g", "SØNDERGAARD THON 200 G",
    "Łukasz Zestaw Narzędzi", "Lukasz Zestaw Narzeczi", "ŁUKASZ ZESTAW NARZĘDZI",
    "Öztürk Tekstil 40x60", "Ozturk Tekstil 40 x 60", "ÖZTÜRK TEKSTİL 40X60",
    "Güneş Lámpara", "Gunes Lampara", "GÜNEŞ LÂMPARA",
    "Digoxin 0,25 mg 30 comprimidos", "Digoxin 0.25 mg", "DIGOXIN 0,25MG 30 TABLETAS",
    "Bromuro de Potasio 100g", "Bromuro de potasio 100 g", "BROMURO POTASIO 100G",
    "Šampú Anticaspa", "Champú Anticaspa", "SHAMPOO ANTICASPA",
    "Perfume Nuit 50ml", "Perfume Nuit 50 ml", "PERFUME NUIT 50ML",
    "Caja Cartón 30x40", "Caja Carton 30 x 40", "CAJA CARTÓN 30X40",
    "Ácido Hialurónico 30ml", "Acido Hialuronico 30 ml",
]
UNIDADES = ["ud", "UND", "unidad", "unidades", "UDS", "pz", "piece"]
SOC_SUFIJOS = ["", "", "", "", " S.A.", " S.L.", " SA", " S.L.U.", " GmbH", " A.S.", " AB", " Sp. z o.o."]


def productos_catalogo(n: int = 4000) -> pd.DataFrame:
    filas = []
    for i in range(n):
        base = RNG.choice(BASE_PRODUCTOS)
        sufijo = RNG.choice(SOC_SUFIJOS)
        filas.append({
            "sku": f"SKU-{i:06d}",
            "descripcion": base + sufijo if sufijo else base,
            "precio": _escalar(_f(1, 400)),
            "unidad_medida": RNG.choice(UNIDADES),
            "familia": RNG.choice(CATEGORIAS),
            "stock": int(NPRNG.integers(0, 500)),
            # True/False reales, no el texto "1"/"0". En el CSV salen como
            # True y False mezclados con S/N/si/no.
            "activo": RNG.choice(["S", "N", "si", "no", "Sí", "No", "1", "0", True, False]),
        })
    df = pd.DataFrame(filas)
    # 10% de precios con error de carga (x100)
    err = df.sample(n=int(len(df) * 0.10), random_state=11).index
    df.loc[err, "precio"] = df.loc[err, "precio"].map(
        lambda x: _escalar(float(x.replace(",", ".")) * 100)
    )
    # 200 precios con 3 decimales y otros 200 sin decimales. Punto, no coma:
    # el resto de la columna va con coma decimal.
    perm = df.sample(n=400, random_state=13).index
    df.loc[perm[:200], "precio"] = [f"{_f(1, 400):.3f}" for _ in range(200)]
    df.loc[perm[200:], "precio"] = [f"{_f(1, 400):.0f}" for _ in range(200)]
    return df


# ---------------------------------------------------------------------------
# 5. LOGISTICA: 3 husos + DST + estados en texto libre
# ---------------------------------------------------------------------------

ESTADOS = [
    "Pendiente", "pendiente", "PENDIENTE", "En tránsito", "En transito", "En transito ",
    "Entregado", "entregado", "Entregado ", " entregado",
    "Devuelto", "devuelto", "Perdido", "perdido", "En reparto", "en reparto",
    "Retrasado", "retrasado", "En espera", "en espera",
]
HUSOS = ["Europe/Madrid", "Europe/Istanbul", "Asia/Dubai"]


def logistica_envios(n: int = 8000) -> pd.DataFrame:
    base = datetime(2024, 1, 1, 9, 0, 0)
    filas = []
    for i in range(n):
        tz = RNG.choice(HUSOS)
        d = _evitar_hueco_dst(
            tz, base + timedelta(days=_d(0, 330), hours=int(NPRNG.integers(0, 24)))
        )
        ts = (
            d.strftime("%Y-%m-%dT%H:%M:%S")
            if RNG.random() < 0.5
            else d.strftime("%Y-%m-%d %H:%M:%S")
        )
        # UTC = hora local MENOS el offset. Sumarlo desplaza el envío al lado
        # contrario. Madrid además cambia de +1 a +2 en verano.
        utc = d - timedelta(hours=_offset_horas(tz, d))
        filas.append({
            "envio_id": f"ENV-{i:06d}",
            "pedido_id": f"PED-{2024000 + int(NPRNG.integers(0, 12000))}",
            "pais_origen": RNG.choice(["ES", "ES", "TR", "AE"]),
            "huso_origen": tz,
            "fecha_envio_local": ts,
            "fecha_envio_utc": utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "peso_kg": _escalar(_f(0.1, 40)),
            "coste_envio": _escalar(_f(3, 60)),
            "estado": RNG.choice(ESTADOS),
            "transportista": RNG.choice(["SEUR", "DHL", "Correos", "Aras", "MRW"]),
        })
    df = pd.DataFrame(filas)
    # Un puñado de envíos cae en los dos domingos de cambio de hora de 2024,
    # para que la conversión de huso no sea un offset constante.
    transiciones = [
        datetime(2024, 3, 31, 1, 15),   # existe, todavía CET (UTC+1)
        datetime(2024, 10, 27, 4, 15),  # existe, ya CET otra vez (UTC+1)
    ]
    for n_fila, momento in enumerate(transiciones):
        for k in range(12):
            idx = n_fila * 12 + k
            d = momento + timedelta(minutes=5 * k)
            tz = "Europe/Madrid"
            sep = "T" if k % 2 == 0 else " "
            df.loc[idx, "huso_origen"] = tz
            df.loc[idx, "pais_origen"] = "ES"
            df.loc[idx, "fecha_envio_local"] = d.strftime(f"%Y-%m-%d{sep}%H:%M:%S")
            utc = d - timedelta(hours=_offset_horas(tz, d))
            df.loc[idx, "fecha_envio_utc"] = utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    nulos = df.sample(n=int(len(df) * 0.03), random_state=17).index
    df.loc[nulos, "peso_kg"] = np.nan
    return df


# ---------------------------------------------------------------------------
# 6. FINANZAS: extracto bancario con formatos monetarios mezclados
# ---------------------------------------------------------------------------

def finanzas_conciliacion(n: int = 6000) -> pd.DataFrame:
    filas = []
    for i in range(n):
        # Cola ancha: si no, casi ningún importe llega a 1.000 y el formato
        # europeo con punto de miles no aparece nunca.
        monto = float(NPRNG.normal(0, 4000))
        if abs(monto) < 1:
            monto = RNG.choice([1.0, -1.0, 10.0, -10.0, 0.0])
        estilo = RNG.random()
        if estilo < 0.40:
            m = _europeo(monto)                  # 1.234,56 o -12,34
        elif estilo < 0.70:
            m = f"{monto:.2f}"                   # americano: 1234.56
        elif estilo < 0.85:
            m = f"{monto:,.2f}"                  # miles americano: 1,234.56
        elif estilo < 0.95:
            m = f"EUR {monto:.2f}"               # con moneda y con signo
        else:
            m = f"({abs(monto):.2f})" if monto < 0 else f"{monto:.2f}"
        d = datetime(2024, 1, 1) + timedelta(days=_d(0, 365))
        filas.append({
            "fecha_operacion": (
                _fecha_erp(d) if RNG.random() < 0.5 else d.strftime("%Y-%m-%d")
            ),
            "concepto": RNG.choice([
                "PAGO TARJETA", "Transferencia recibida", "Pago Bizum", "Recibo",
                "DOMICILIACION", "Reintegro", "COMPRA", "Devolucion",
            ]),
            "importe": m,
            "saldo": _escalar(_f(-10000, 50000)),
            "referencia": f"REF-{i:06d}",
            "conciliado": RNG.choice(["S", "N", "", "sí", "no"]),
        })
    df = pd.DataFrame(filas)
    # 8% de filas comparten referencia con OTRA fila, en parejas.
    # No es un duplicado de movimiento: son dos apuntes a conciliar.
    n_par = int(len(df) * 0.08)
    n_par -= n_par % 2
    idxs = list(df.sample(n=n_par, random_state=19).index)
    for izquierda, derecha in zip(idxs[::2], idxs[1::2]):
        df.loc[derecha, "referencia"] = df.loc[izquierda, "referencia"]
    return df


# ---------------------------------------------------------------------------
# 7. RRHH: nominas con columnas por anio (para melt/pivot)
# ---------------------------------------------------------------------------

def rrhh_nominas(n: int = 800) -> pd.DataFrame:
    filas = []
    for i in range(n):
        filas.append({
            "empleado_id": i + 1,
            "nombre": f"{RNG.choice(NOMBRES['ES'] + NOMBRES['DE'] + NOMBRES['SE'] + NOMBRES['PL'] + NOMBRES['AE'])} "
                      f"{RNG.choice(APELLIDOS['ES'] + APELLIDOS['DE'] + APELLIDOS['SE'] + APELLIDOS['PL'] + APELLIDOS['AE'])}",
            "pais": RNG.choice(["ES", "ES", "ES", "DE", "SE", "PL", "AE"]),
            "departamento": RNG.choice([
                "Ventas", "Tecnologia", "Finanzas", "RRHH", "Logistica", "Marketing",
            ]),
            "salario_base": _escalar(24000 + _f(-4000, 9000)),
            "plus_2022": _escalar(_f(0, 3000)),
            "plus_2023": _escalar(_f(0, 3000)),
            "plus_2024": _escalar(_f(0, 3000)),
            "bajas_2024": RNG.choice([0, 0, 0, 0, 1]),
        })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 8. ENCUESTAS: Likert como texto + HTML entities + emojis
# ---------------------------------------------------------------------------

LIKERT = [
    "Muy mal", "Mal", "Normal", "Bien", "Muy bien", "muy bien", "BIEN", "Bien ",
    "Excelente", "excelente", "5", "4", "3", "2", "1", "ns/nc", "N/S", "-",
]


def encuestas_satisfaccion(n: int = 2500) -> pd.DataFrame:
    filas = []
    for i in range(n):
        filas.append({
            "respuesta_id": i + 1,
            "enviado": (
                datetime(2024, 1, 1) + timedelta(days=_d(0, 300))
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "satisfaccion": RNG.choice(LIKERT),
            "velocidad_envio": RNG.choice(LIKERT),
            "calidad_producto": RNG.choice(LIKERT),
            "recomendaria": RNG.choice([
                "Sí", "si", "Sí", "No", "no", "Quizás", "1", "0", "",
            ]),
            "comentario": RNG.choice([
                "El producto &amp; arrived bien", "Nada que decir", "Very good!",
                "Llegó tarde 😞", "Excelente servicio 👍", "&lt;excelente&gt;",
                "malo &amp; caro", "Tardó 3 semanas", "TODO bien", "NN/NN",
                "Café ☕ perfecto", "Naïve façade", "Straße señal",
            ]),
        })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Escritura con separadores / encodings distintos
# ---------------------------------------------------------------------------

def guardar_todo(out: Path, seed: int = 42) -> None:
    global RNG, NPRNG
    RNG = random.Random(seed)
    NPRNG = np.random.default_rng(seed)

    out.mkdir(parents=True, exist_ok=True)

    # 1. ERP espanol: ';' + decimal ',' + latin-1 + dd/mm/yyyy
    ventas_este().to_csv(
        out / "ventas_2024_este.csv", sep=";", decimal=",", index=False,
        encoding="latin-1", lineterminator="\n",
    )
    # 2. ERP rama oeste: TAB + punto decimal + ISO dates + utf-8
    ventas_oeste().to_csv(out / "ventas_2024_oeste.tsv", sep="\t", index=False, encoding="utf-8")
    # 3. CRM: utf-8 con BOM (así lo exporta Excel)
    clientes_crm().to_csv(out / "clientes_crm.csv", index=False, encoding="utf-8-sig")
    # 4. Maestro de productos
    productos_catalogo().to_csv(out / "productos_catalogo.csv", index=False, encoding="utf-8")
    # 5. API de paquetería
    logistica_envios().to_csv(out / "logistica_envios.csv", index=False, encoding="utf-8")
    # 6. Extracto bancario: ';' + formatos monetarios mezclados + latin-1
    finanzas_conciliacion().to_csv(
        out / "finanzas_conciliacion.csv", sep=";", index=False, encoding="latin-1"
    )
    # 7. Nóminas: XLSX con índice + columnas por año
    rr = rrhh_nominas().set_index("empleado_id")
    rr.to_excel(out / "rrhh_nominas.xlsx", sheet_name="nominas")
    # 8. Encuestas
    encuestas_satisfaccion().to_csv(out / "encuestas_satisfaccion.csv", index=False, encoding="utf-8")

    print("Datasets generados en:", out.resolve())
    print("-" * 58)
    for f in sorted(out.iterdir()):
        print(f"  {f.name:30} {f.stat().st_size / 1024:9.1f} KB")

    # Respuesta esperada de la auditoría de carga (L01). Si cambias la
    # suciedad de arriba, cambia también estas tres líneas.
    informe = [
        ("ventas_2024_este.csv", ";", "latin-1",
         "coma decimal; fechas dd/mm/yyyy; 5% de Descuento % vacío"),
        ("ventas_2024_oeste.tsv", "TAB", "utf-8",
         "punto decimal; fechas ISO; esquema distinto al del este"),
        ("clientes_crm.csv", ",", "utf-8-sig",
         "BOM; 400 duplicados exactos; variantes de nombre del mismo cliente_id"),
        ("productos_catalogo.csv", ",", "utf-8",
         "precios x100; 200 con 3 decimales y 200 sin decimales; activo mezclado con True/False"),
        ("logistica_envios.csv", ",", "utf-8",
         "UTC = local menos offset; DST de Madrid 2024; 3% de peso nulo"),
        ("finanzas_conciliacion.csv", ";", "latin-1",
         "5 formatos de importe, incluido 1.234,56; referencias repetidas por parejas; EUR conserva el signo"),
        ("rrhh_nominas.xlsx", "(excel)", "(xlsx)",
         "índice en empleado_id; importes con coma; columnas plus_año para melt"),
        ("encuestas_satisfaccion.csv", ",", "utf-8",
         "Likert mezclado con números; N/S, ns/nc y NN/NN; HTML y emojis"),
    ]
    print("\nAnomalías sembradas (lo que la auditoría debería encontrar):")
    for nombre, sep, enc, anom in informe:
        print(f"  {nombre:30} sep={sep:8} enc={enc:10} {anom}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="datos", help="carpeta de salida")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    guardar_todo(Path(args.out), args.seed)
