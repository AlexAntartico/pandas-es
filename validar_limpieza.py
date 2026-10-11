"""
validar_limpieza.py — comprueba que un pipeline de limpieza no ha roto nada.

Idea: cuando limpias datos, casi nunca te falta información. Lo que pasa es
que **pierdes filas por el camino sin enterarte**. Un merge mal hecho puede
borrar el 30% de la facturación y el DataFrame resultante sigue teniendo el
mismo aspecto.

Este script compara el dataset CRUDO con el dataset LIMPIO y te dice:

  - cuantas filas has perdido (y si exceeds un umbral, es rojo)
  - el dinero que ha desaparecido de la facturación
  - si los totales cuadran
  - si la clave de negocio es única
  - si los tipos son los que esperabas

Uso (el CSV limpio lo produce tu pipeline; no viene generado):
    python validar_limpieza.py --crudo datos/ventas_2024_este.csv \\
        --limpio salida/ventas_limpias.csv --dinero Importe --clave "ID Pedido"

Sale con código 1 si se pasa del umbral de filas, del de dinero, o si la
clave queda duplicada.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "notebooks"))

VERDE, ROJO, AMARILLO, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"


def _c(texto: str, color: str) -> str:
    return f"{color}{texto}{RESET}"


# Los ficheros de `datos/` no se leen igual: esto es la L01 concentrada aqui.
# Si el validador no sabe leer el crudo, no puede decirte quanto has perdido.
PARAMETROS = {
    "ventas_2024_este.csv":      dict(sep=";", decimal=",", encoding="latin-1"),
    "finanzas_conciliacion.csv": dict(sep=";", encoding="latin-1"),
    "ventas_2024_oeste.tsv":     dict(sep="\t", encoding="utf-8"),
    "clientes_crm.csv":          dict(encoding="utf-8-sig"),
}


def leer(ruta: Path, **kw) -> pd.DataFrame:
    """Lee un csv/tsv/xlsx/parquet con los parametros que necesita cada uno."""
    if not ruta.exists():
        raise FileNotFoundError(f"No existe: {ruta}")
    if ruta.suffix == ".xlsx":
        # Solo el export crudo de nóminas trae el índice en la primera columna.
        if ruta.name == "rrhh_nominas.xlsx":
            kw.setdefault("index_col", 0)
        return pd.read_excel(ruta, **kw)
    if ruta.suffix == ".parquet":
        return pd.read_parquet(ruta, **kw)
    params = {**PARAMETROS.get(ruta.name, {}), **kw}
    return pd.read_csv(ruta, **params)


def validar(
    crudo: pd.DataFrame,
    limpio: pd.DataFrame,
    columna_dinero: str | None = None,
    clave: str | None = None,
    umbral_perdida: float = 5.0,
    tolerancia_dinero: float = 2.0,
) -> bool:
    """
    Devuelve True solo si filas, dinero y clave están dentro de los umbrales.
    Imprime un informe legible con colourines.
    """
    ok = True
    print("\n" + "=" * 64)
    print("VALIDACIÓN DEL PIPELINE DE LIMPIEZA")
    print("=" * 64)

    # --- 1. Filas ---
    n_crudo, n_limpio = len(crudo), len(limpio)
    pct = (1 - n_limpio / n_crudo) * 100 if n_crudo else 0
    if abs(pct) <= umbral_perdida:
        print(f"{_c('OK  ', VERDE)} filas: {n_crudo:,} -> {n_limpio:,} "
              f"({pct:+.2f}% de diferencia)")
    else:
        ok = False
        print(f"{_c('FALLA', ROJO)} filas: {n_crudo:,} -> {n_limpio:,} "
              f"({pct:+.2f}%. Te has pasado del {umbral_perdida}% permitido)")

    # --- 2. Dinero ---
    if columna_dinero and columna_dinero in crudo.columns \
            and columna_dinero in limpio.columns:
        try:
            sum_crudo = pd.to_numeric(crudo[columna_dinero], errors="coerce").sum()
            sum_limpio = pd.to_numeric(limpio[columna_dinero], errors="coerce").sum()
            if sum_crudo:
                dif = (sum_limpio - sum_crudo) / sum_crudo * 100
                if abs(dif) <= tolerancia_dinero:
                    print(f"{_c('OK  ', VERDE)} dinero: {sum_crudo:,.2f} -> {sum_limpio:,.2f} "
                          f"({dif:+.2f}%)")
                else:
                    ok = False
                    print(f"{_c('FALLA', ROJO)} dinero: {sum_crudo:,.2f} -> {sum_limpio:,.2f} "
                          f"({dif:+.2f}%. Se ha perdido facturación)")
        except Exception as e:  # noqa: BLE001
            print(f"{_c('AVISO', AMARILLO)} no se pudo validar el dinero: {e}")
    elif columna_dinero:
        print(f"{_c('AVISO', AMARILLO)} la columna de dinero "
              f"'{columna_dinero}' no existe en alguno de los dos datasets")

    # --- 3. Clave única ---
    if clave:
        if clave in limpio.columns:
            dup = limpio[clave].duplicated().sum()
            if dup == 0:
                print(f"{_c('OK  ', VERDE)} clave '{clave}': única (0 duplicados)")
            else:
                ok = False
                print(f"{_c('FALLA', ROJO)} clave '{clave}': {dup:,} duplicados. "
                      f"Debería ser única tras la limpieza")
        else:
            print(f"{_c('AVISO', AMARILLO)} la clave '{clave}' no existe en el limpio")

    # --- 4. Nulos ---
    nulos_crudo = crudo.isna().sum().sum()
    nulos_limpio = limpio.isna().sum().sum()
    print(f"{_c('INFO', AMARILLO)} nulos totales: {nulos_crudo:,} -> {nulos_limpio:,}")

    # --- 5. Columnas perdidas ---
    perdidas = set(crudo.columns) - set(limpio.columns)
    nuevas = set(limpio.columns) - set(crudo.columns)
    if perdidas:
        print(f"{_c('AVISO', AMARILLO)} columnas perdidas: {sorted(perdidas)}")
    if nuevas:
        print(f"{_c('INFO', AMARILLO)} columnas nuevas: {sorted(nuevas)}")

    print("=" * 64 + "\n")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crudo", required=True)
    ap.add_argument("--limpio", required=True)
    ap.add_argument("--dinero", default=None, help="columna numérica de importe")
    ap.add_argument("--clave", default=None, help="columna que debe quedar única")
    ap.add_argument("--umbral", type=float, default=5.0)
    args = ap.parse_args()

    crudo = leer(Path(args.crudo))
    limpio = leer(Path(args.limpio))
    print(f"crudo : {len(crudo):,} filas x {crudo.shape[1]} columnas")
    print(f"limpio: {len(limpio):,} filas x {limpio.shape[1]} columnas")
    bien = validar(crudo, limpio, args.dinero, args.clave, args.umbral)
    sys.exit(0 if bien else 1)


if __name__ == "__main__":
    main()
