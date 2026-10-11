"""
herramientas.py — helpers de apoyo para los notebooks de la Ruta Pandas.

Se importa desde cualquier notebook con:

    from herramientas import mostrar, guardar_excel, guardar_figura, ficha

Nada de esto es obligatorio: es un andamio para que los entregables de los
workbooks salgan con formato y se puedan pegar en un PDF o mandar por correo.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Rutas del proyecto
# --------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
SALIDA = RAIZ / "salida"
SALIDA.mkdir(exist_ok=True)


# --------------------------------------------------------------------------
# 1. Mostrar DataFrames sin reventar el notebook
# --------------------------------------------------------------------------

def mostrar(df: pd.DataFrame, n: int = 12, titulo: str = "") -> None:
    """
    Muestra las primeras n filas como texto.

    Existe porque `df.head(200)` dentro de un notebook mete 200 líneas de HTML
    y a partir de la semana 3 no vas a poder leer tu propio notebook.
    """
    if titulo:
        print(f"\n=== {titulo} ===")
    if len(df) > n:
        print(f"[{len(df):,} filas en total, mostrando {n}]")
    print(df.head(n).to_string(index=False))


def perfil_memoria(df: pd.DataFrame) -> pd.DataFrame:
    """Desglose de memoria por columna, ordenado de mayor a menor."""
    mem = df.memory_usage(deep=True)
    total = mem.sum()
    out = pd.DataFrame({
        "memoria_bytes": mem,
        "porcentaje": (mem / total * 100).round(2),
    }).sort_values("memoria_bytes", ascending=False)
    out["memoria_bytes"] = out["memoria_bytes"].map(
        lambda b: f"{b / 1024**2:8.2f} MB"
    )
    return out


# --------------------------------------------------------------------------
# 2. Ficha técnica de un dataset (la L02, reutilizable)
# --------------------------------------------------------------------------

# Valores que significan "no hay dato" pero no son NaN de verdad.
FALSOS_NULOS = {
    "", " ", "-", "--", "?", "n/a", "N/A", "na", "NA", "null", "NULL", "None",
    "none", "sin dato", "SIN DATO", "s/d", "#N/A", "#VALOR!", "NaN", "nan",
    "nd", "N/D", "s/n", "S/N", "ns/nc", "N/S", "NN/NN", "sin informacion",
    "desconocido",
}


def contar_falsos_nulos(serie: pd.Series) -> pd.Series:
    """
    Cuenta, por valor, cuántas filas son 'nulos de mentira'.

    `isna()` solo ve los NaN de verdad. Un "N/A" escrito por un humano es un
    nulo para cualquier reporte, y `isna()` no lo detecta. La comparación es
    sin distinción de mayúsculas: "NN/NN", "#N/A" y "N/D" cuentan.
    """
    s = serie.astype("string").str.strip()
    falsos = {v.casefold() for v in FALSOS_NULOS}
    norm = s.str.casefold().isin(falsos)
    return serie[norm.fillna(False)].value_counts(dropna=False)


def ficha(df: pd.DataFrame, nombre: str = "dataset") -> pd.DataFrame:
    """
    Devuelve el perfil de calidad de un DataFrame, una fila por columna.

    Sirve para la L07 y para el informe de calidad del capstone.
    """
    filas = []
    for col in df.columns:
        s = df[col]
        n = len(s)
        nulos_reales = int(s.isna().sum())
        falsos = int(contar_falsos_nulos(s).sum())
        filas.append({
            "columna": col,
            "dtype": str(s.dtype),
            "nulos_reales": nulos_reales,
            "%_nulos": round(nulos_reales / n * 100, 2) if n else 0.0,
            "falsos_nulos": falsos,
            "%_falsos_nulos": round(falsos / n * 100, 2) if n else 0.0,
            "unicos": int(s.nunique(dropna=True)),
            "cardinalidad_%": round(s.nunique(dropna=True) / n * 100, 2) if n else 0.0,
            "duplicados": int(s.duplicated().sum()),
        })
    out = pd.DataFrame(filas)
    print(f"\n=== FICHA: {nombre} ===")
    print(f"filas: {len(df):,} | columnas: {df.shape[1]} | "
          f"memoria: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    return out


# --------------------------------------------------------------------------
# 3. Normalización de texto multilingüe (la L09 y la L10)
# --------------------------------------------------------------------------

def quitar_espacios(s: pd.Series) -> pd.Series:
    """Espacios/tabs/saltos al principio, al final y repetidos en el medio."""
    return (
        s.astype("string")
        .str.strip()
        .str.replace(r"[\s   ]+", " ", regex=True)
    )


def quitar_acentos(s: pd.Series) -> pd.Series:
    """
    NFKD separa la 'á' en 'a' + tilde combinante; quitamos la combinante.
    OJO: no lo apliques a un sistema donde 'a' y 'á' son categorias distintas.
    """
    norm = s.astype("string").str.normalize("NFKD")
    return norm.str.replace(r"[̀-ͯ]", "", regex=True)


# Letras latinas que NO son una base + diacrítico. NFKD no las separa.
# ş (cedilla, turco, U+015F), ș (coma, rumano, U+0219) y ś (acento, polaco,
# U+015B) se ven casi iguales y aquí se reducen las tres a "s" a propósito:
# esa decisión puede fusionar personas distintas.
#
# ä/ö/ü se reducen a a/o/u (se quita el diacrítico), no a ae/oe/ue.
# Con esa regla Söderberg y Soderberg coinciden, y Müller y Mueller no.
# La regla alemana inversa fusionaría el otro par y separaría este.
# Una sola clave no puede hacer las dos cosas.
TRANSLIT = {
    "\u0141": "L", "\u0142": "l",   # L con barra     (polaco)
    "\u00d8": "O", "\u00f8": "o",   # O con trazo     (danés/noruego)
    "\u0152": "OE", "\u0153": "oe", # OE ligadura     (francés)
    "\u00c6": "AE", "\u00e6": "ae", # AE ligadura     (islandés/danés)
    "\u0110": "D", "\u0111": "d",   # D con trazo     (croata)
    "\u00de": "TH", "\u00fe": "th", # Thorn           (islandés)
    "\u00d0": "D", "\u00f0": "d",   # Eth             (islandés)
    "\u015e": "S", "\u015f": "s",   # S con cedilla   (turco)
    "\u0218": "S", "\u0219": "s",   # S con coma      (rumano)   <-- NO es el turco
    "\u015a": "S", "\u015b": "s",   # S con acento    (polaco)   <-- NO es el turco
    "\u0179": "Z", "\u017a": "z",   # Z con punto     (polaco)
    "\u017b": "Z", "\u017c": "z",   # Z con trazo     (polaco)
    "\u0130": "I",                   # I con punto     (turco)    <-- CRITICO
    "\u0131": "i",                   # i sin punto     (turco)    <-- CRITICO
    "\u011e": "G", "\u011f": "g",   # G con brevis    (turco)
    "\u00c7": "C", "\u00e7": "c", "\u00d1": "N", "\u00f1": "n",
    "\u00c1": "A", "\u00e1": "a", "\u00c4": "A", "\u00e4": "a",
    "\u00c0": "A", "\u00e0": "a", "\u00c3": "A", "\u00e3": "a",
    "\u00c5": "A", "\u00e5": "a", "\u00c9": "E", "\u00e9": "e",
    "\u00c8": "E", "\u00ea": "e", "\u00cb": "E",
    "\u00eb": "e", "\u00cd": "I", "\u00ed": "i", "\u00ce": "I",
    "\u00cf": "I", "\u00ee": "i", "\u00d3": "O", "\u00f3": "o",
    "\u00d4": "O", "\u00f4": "o", "\u00d6": "O", "\u00f6": "o",
    "\u00da": "U", "\u00fa": "u", "\u00dc": "U", "\u00fc": "u",
    "\u00dd": "Y", "\u00fd": "y", "\u00df": "ss",  # ß: SI se expande
    "\u010d": "c", "\u0107": "c",
    "\u00b5": "u", "\u2013": "-", "\u2014": "-", "\u2018": "'",
    "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u00a0": " ",
}


def transliterar_latin(s: str) -> str:
    """
    Translitera SOLO lo que pertenece al alfabeto latino.

    `unidecode` sobre todo el texto convierte también el árabe a una
    aproximación latina ('محمد' -> 'mhmd'). Eso sustituye el nombre por otro
    idioma. Los caracteres no latinos se quedan; solo se les quitan las marcas.
    """
    if pd.isna(s):
        return s
    s = str(s)
    # 1. resolver primero las ligaduras y tes que NFKD no separa
    s = s.replace("\ufb00", "ff").replace("\ufb01", "fi").replace("\ufb02", "fl")
    s = s.replace("\u00c5", "A").replace("\u0130", "I")
    # 2. los caracteres arabes van con marcas harakat (U+064B-0652) y
    #    marcas de direccion (U+200E/200F): se quitan, no se transliteran
    s = "".join(
        c for c in s
        if not (0x064B <= ord(c) <= 0x0652 or ord(c) in (0x200E, 0x200F, 0x061C))
    )
    s = "".join(TRANSLIT.get(c, c) for c in s)
    # 3. ahora si, descomponer y quitar diacriticos (solo afecta al latin)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", s)


def a_ascii(s: pd.Series) -> pd.Series:
    """
    Version ASCII pura. Solo usala si TU pipeline entero es ASCII
    (comparar contra un maestro antiguo, por ejemplo).

    Riesgo real: funde 'Łukasz' y 'Lukasz', y convierte 'محمد' en 'mhmd'.
    Midelo antes de decidir. Necesita el paquete `unidecode`.
    """
    from unidecode import unidecode

    return s.astype("string").map(
        lambda v: "".join(
            ch for ch in (unidecode(v) if pd.notna(v) else v)
            if ch.isascii()
        ) if pd.notna(v) else v
    )


def clave_canonica(s: pd.Series, solo_latin: bool = False) -> pd.Series:
    """
    Clave de deduplicacion para texto en cualquier alfabeto.

    El orden importa:

      1. colapsar espacios invisibles y repetidos
      2. `casefold` (más agresivo que `lower`: 'ß' pasa a 'ss', 'İ' pasa a
         'i' más un combinante). 'I'.casefold() da 'i'. En turco la minúscula
         de 'I' es 'ı'. El paso 3 mapea 'ı' e 'İ' a 'i': es una decisión
         de negocio, no la regla turca de locale.
      3. transliterar el latín extendido ('ł' a 'l', 'ø' a 'o', 'ı' a 'i')
      4. NFKD y quitar diacríticos, también el hamza y el tashkil que queden
         como marcas combinantes
      5. tirar la puntuación. Con `solo_latin=False` el árabe y el cirílico
         se conservan. No se pasan a ASCII.

    'محمد' no debe acabar vacío: eso fundiría a todos los clientes árabes.
    Riesgo que esta clave sí acepta: 'Łukasz' y 'Lukasz' se funden.
    Mídelo con `auditar_fusiones`.
    """
    out = s.astype("string")
    out = out.str.replace(r"[\s   ]+", " ", regex=True)
    out = out.str.strip()
    out = out.str.casefold()
    out = out.map(lambda v: transliterar_latin(v) if pd.notna(v) else v)
    if solo_latin:
        out = out.str.replace(r"[^a-z0-9]+", " ", regex=True)
    else:
        out = out.str.replace(r"[^\w\s-]", " ", regex=True, flags=re.UNICODE)
        out = out.str.replace(r"\s+", " ", regex=True)
    return out.str.strip()


def auditar_fusiones(
    df: pd.DataFrame,
    columna: str = "nombre",
    clave: str | pd.Series = "clave_canonica",
    contexto: tuple[str, ...] = ("email", "pais"),
    n: int = 15,
) -> pd.DataFrame:
    """
    Devuelve los grupos que la clave canonica ha FUSIONADO, con el contexto
    necesario para decidir si la fusion es correcta.

    `clave` admite un nombre de columna o directamente la Serie, que es como
    se usa de verdad:

        c["clave"] = clave_canonica(c["nombre"])
        auditar_fusiones(c, "nombre", clave=c["clave"])

    Por que importa: 'he colapsado 8.659 filas a 982 clientes' suena a un
    exito del 88%. Hasta que ves que ha fusionado '\u0141ukasz' con 'Lukasz',
    '\u00c7eker' con 'Seker' y dos personas arabes distintas en una, no sabes
    cuanto de ese 88% es senal y cuanto es dano.
    """
    cols_ctx = [c for c in contexto if c in df.columns]
    temp = df[[columna, *cols_ctx]].copy()
    temp["_clave"] = clave if isinstance(clave, pd.Series) else temp[clave]
    temp["_clave"] = temp["_clave"].fillna("<nulo>").astype(str)

    g = temp.groupby("_clave", dropna=False).agg(
        variantes=(columna, lambda s: sorted({str(v) for v in s})),
        n_filas=(columna, "size"),
        **{c: (c, "nunique") for c in cols_ctx},
    )
    # solo nos interesan los grupos donde la clave unifico escrituras DISTINTAS
    g = g[g["variantes"].map(len) > 1].copy()
    g = g.sort_values("n_filas", ascending=False)

    total_fusiones = int(g["n_filas"].sum() - len(g))
    print(f"\nFusiones: {len(g):,} grupos han unificado escrituras distintas "
          f"({total_fusiones:,} filas de mas colapsadas).")
    if cols_ctx:
        g = g.assign(**{c: g[c].map(lambda n: n if n > 1 else "") for c in cols_ctx})
    print(f"Revisar los {min(n, len(g))} mas grandes:\n")
    if len(g):
        mostrar(g.head(n).reset_index(drop=True), n=n, titulo="GRUPOS A REVISAR")
    return g.head(n).reset_index(drop=True)


def detectar_alfabeto(serie: pd.Series) -> pd.Series:
    """
    Etiqueta cada valor con su script principal: latin / arabic / greek / ...

    Util antes de decidir como normalizar: te dice si una columna mezcla
    alfabetos, y por tanto si 'un solo pipeline de limpieza' es viable.
    """
    def _script(v) -> str:
        if pd.isna(v):
            return "nulo"
        for ch in str(v):
            if not ch.isalpha():
                continue
            try:
                nombre = unicodedata.name(ch)
            except ValueError:
                continue
            for clave, etiqueta in (
                ("LATIN", "latin"), ("ARABIC", "arabic"), ("GREEK", "greek"),
                ("CYRILLIC", "cyrillic"), ("HEBREW", "hebrew"), ("CJK", "cjk"),
            ):
                if clave in nombre:
                    return etiqueta
        return "otro"
    return serie.astype("string").map(_script)


# --------------------------------------------------------------------------
# 4. Parseo de importes y fechas (la L08)
# --------------------------------------------------------------------------

def parsear_importes(serie: pd.Series) -> pd.Series:
    """
    Convierte a float estos formatos:
        1.234,56      (europeo: punto de miles y coma decimal)
        1234,56       (europeo sin separador de miles)
        1234.56       (americano)
        1,234.56      (americano con coma de miles)
        EUR 1234.56   (con moneda; el signo se conserva)
        (1234.56)     (paréntesis = negativo)
        1 234,56      (espacio de miles)

    `1.234` con un solo punto se queda en 1.234. Es ambiguo: sin la coma de
    `1.234,56` no hay forma de saber si el punto separa miles.
    """
    def _uno(v):
        if pd.isna(v):
            return np.nan
        s = str(v).strip()
        negativo = False
        if s.startswith("(") and s.endswith(")"):
            negativo, s = True, s[1:-1]
        s = re.sub(r"[^\d,.\-]", "", s)          # fuera EUR, espacios, signos
        if s.count(",") and s.count("."):
            # el separador decimal es el que aparece más a la derecha
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif s.count(",") == 1:
            # una sola coma: decimal (1.234 puede ser miles, no decimal)
            s = s.replace(",", ".")
        elif s.count(",") > 1:
            s = s.replace(",", "")
        try:
            out = float(s)
        except ValueError:
            return np.nan
        return -out if negativo else out
    return serie.map(_uno)


def parsear_fecha(serie: pd.Series, formato: str = "%d/%m/%Y") -> pd.Series:
    """
    Convierte a datetime pasando SIEMPRE el formato.

    `pd.to_datetime(s)` a secas adivina, y con fechas tipo '01/02/2024'
    (ambiguas: ¿1 de febrero o 2 de enero?) falla en silencio o lanza
    FutureWarning. Nunca adivines el formato.
    """
    # Con `format=` pandas ignora `dayfirst`. No lo pases: solo añade un aviso.
    return pd.to_datetime(serie, format=formato, errors="coerce")


# --------------------------------------------------------------------------
# 5. Exportación: a disco, en el formato que te pidan
# --------------------------------------------------------------------------

def guardar_excel(
    df: pd.DataFrame,
    nombre: str,
    hoja: str = "datos",
    anchos: bool = True,
    congelar: str = "A2",
    formatear_importe: str | None = None,
) -> Path:
    """
    Escribe un .xlsx decente: cabecera con fondo, anchos ajustados, autofiltro
    y la primera fila congelada. Sin esto, el fichero se ve como un volcado
    de base de datos y nadie lo abre dos veces.
    """
    ruta = SALIDA / (nombre if nombre.endswith(".xlsx") else f"{nombre}.xlsx")
    with pd.ExcelWriter(ruta, engine="xlsxwriter") as xw:
        df.to_excel(xw, sheet_name=hoja[:31], index=False, startrow=0)
        libro, ws = xw.book, xw.sheets[hoja[:31]]
        fmt_cab = libro.add_format({
            "bold": True, "bg_color": "#1F3864", "font_color": "white",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        for c, col in enumerate(df.columns):
            ws.write(0, c, str(col), fmt_cab)
            if anchos:
                ancho = min(max(len(str(col)) + 2,
                                int(df[col].astype(str).str.len().quantile(0.9)) + 2), 42)
                ws.set_column(c, c, ancho)
        if len(df):
            ws.autofilter(0, 0, len(df), len(df.columns) - 1)
        if congelar:
            # 'A2' o 'AA2' -> (fila, columna) en enteros, base 0.
            ref = re.fullmatch(r"([A-Z]+)(\d+)", congelar.strip().upper())
            if ref is None:
                raise ValueError(f"congelar debe ser una celda tipo 'A2', no {congelar!r}")
            letras, num = ref.group(1), int(ref.group(2))
            col_idx = 0
            for ch in letras:
                col_idx = col_idx * 26 + (ord(ch) - ord("A") + 1)
            # 'A2' en Excel = la primera celda visible es la fila 2. xlsxwriter
            # cuenta desde 0, así que la fila visible es num-1.
            ws.freeze_panes(num - 1, col_idx - 1)

        # El formato numérico se aplica a las CELDAS, no a la columna: pasar un
        # Format a set_column sobrescribe el ancho que acabamos de calcular.
        if formatear_importe:
            fmt_imp = libro.add_format({"num_format": formatear_importe})
            for col_i, col in enumerate(df.columns):
                if not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                for fila, valor in enumerate(df[col].to_numpy(), start=1):
                    if pd.isna(valor):
                        continue
                    ws.write_number(fila, col_i, float(valor), fmt_imp)
    print(f"  [excel] {ruta.name}  ({len(df):,} filas)")
    return ruta


def guardar_csv(df: pd.DataFrame, nombre: str, decimal: str = ".", sep: str = ",") -> Path:
    """CSV con encoding utf-8-sig para que Excel en español no rompa los acentos."""
    ruta = SALIDA / (nombre if nombre.endswith(".csv") else f"{nombre}.csv")
    df.to_csv(ruta, index=False, sep=sep, decimal=decimal, encoding="utf-8-sig")
    print(f"  [csv]    {ruta.name}  ({len(df):,} filas)")
    return ruta


def guardar_figura(fig, nombre: str, formatos=("png", "svg", "pdf"), dpi: int = 200) -> list[Path]:
    """
    Exporta una figura de matplotlib a varios formatos.

      png -> pegar en slides, documentos, emails
      svg -> vectorial, escala sin perder nitidez (para imprimir)
      pdf -> el formato que exige casi todo proceso de publication

    `bbox_inches='tight'` es OBLIGATORIO: sin él, matplotlib recorta las
    etiquetas de los ejes y el fichero sale con media leyenda fuera.
    """
    rutas = []
    for ext in formatos:
        ruta = SALIDA / f"{nombre}.{ext}"
        fig.savefig(ruta, dpi=dpi, bbox_inches="tight", facecolor="white")
        print(f"  [fig]    {ruta.name}  ({ruta.stat().st_size / 1024:.0f} KB)")
        rutas.append(ruta)
    return rutas


def guardar_html(fig, nombre: str) -> Path:
    """HTML autocontenido de una figura plotly (funciona offline, pesa ~4 MB)."""
    ruta = SALIDA / f"{nombre}.html"
    fig.write_html(str(ruta), include_plotlyjs=True, full_html=True)
    print(f"  [html]   {ruta.name}")
    return ruta


def _aplanar(items) -> list[Path]:
    """
    `guardar_figura` devuelve una lista (png, svg, pdf) y `guardar_excel` un Path.
    `resumen_entrega` tiene que poder recibir las dos cosas sin que el alumno
    tenga que acordarse de cuál es cuál.
    """
    out: list[Path] = []
    for it in items:
        if isinstance(it, (list, tuple, set)):
            out.extend(Path(x) for x in it)
        else:
            out.append(Path(it))
    return out


def resumen_entrega(*rutas) -> None:
    """Imprime el manifiesto de lo que ha producido un notebook."""
    print("\n" + "=" * 62)
    print("ENTREGABLES DE ESTE NOTEBOOK")
    print("=" * 62)
    total = 0
    for r in _aplanar(rutas):
        if r.exists():
            kb = r.stat().st_size / 1024
            total += kb
            print(f"  {r.name:42} {kb:9.1f} KB")
        else:
            print(f"  {r.name:42}   NO EXISTE")
    print(f"  {'TOTAL':42} {total:9.1f} KB")
    print(f"\n  Carpeta: {SALIDA}")


# --------------------------------------------------------------------------
# 6. Carga de datasets con los parámetros correctos
# --------------------------------------------------------------------------

# Los ficheros de `datos/` NO se pueden leer igual. Esta tabla es la trampa
# de la L01 concentrada en un sitio.
PARAMETROS_DATOS = {
    "ventas_2024_este.csv":    dict(sep=";", decimal=",", encoding="latin-1"),
    "ventas_2024_oeste.tsv":   dict(sep="\t", encoding="utf-8"),
    "clientes_crm.csv":        dict(encoding="utf-8-sig"),
    "productos_catalogo.csv":  dict(encoding="utf-8"),
    "logistica_envios.csv":    dict(encoding="utf-8"),
    "finanzas_conciliacion.csv": dict(sep=";", encoding="latin-1"),
    "encuestas_satisfaccion.csv": dict(encoding="utf-8"),
}


def cargar(nombre, **extra) -> pd.DataFrame:
    """
    Carga un dataset de `datos/` con sus parámetros correctos ya puestos.

    Acepta un `str` ("clientes_crm.csv") o un `Path`. Los .xlsx se leen con
    `index_col=0` porque rrhh_nominas.xlsx se guardó con el índice en la
    primera columna.
    """
    nombre = Path(nombre).name          # normaliza: da igual str que Path
    if nombre.endswith(".xlsx"):
        return pd.read_excel(DATOS / nombre, index_col=0, **extra)
    params = {**PARAMETROS_DATOS.get(nombre, {}), **extra}
    return pd.read_csv(DATOS / nombre, **params)
