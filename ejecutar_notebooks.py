"""
ejecutar_notebooks.py — verifica que el código de cada celda funciona de verdad.

No ejecuta Jupyter (no hace falta): extrae las celdas de código del .ipynb, las
convierte a un script y las ejecuta en un único espacio de nombres, que es
exactamente como se comportan las celdas de un notebook.

Un .ipynb válido en formato, con código roto, no sirve de nada. Esto lo comprueba.
"""

from __future__ import annotations

import io
import json
import os
import sys
import traceback
import warnings
from contextlib import redirect_stdout
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
warnings.filterwarnings("ignore", message="FigureCanvasAgg is non-interactive")

RAIZ = Path(__file__).resolve().parent
NOTEBOOKS = RAIZ / "notebooks"


def celdas_de_codigo(ruta: Path) -> list[str]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in datos["cells"]
            if c["cell_type"] == "code"]


def ejecutar(ruta: Path) -> bool:
    codigo = celdas_de_codigo(ruta)
    guiones = "\n\n".join(f"# ---- celda {i + 1} ----\n{c}" for i, c in enumerate(codigo))
    # Los notebooks leen `datos/` desde la raíz del proyecto, que es también
    # el directorio de trabajo de `jupyter lab --notebook-dir=.`.
    cwd = os.getcwd()
    os.chdir(RAIZ)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(compile(guiones, str(ruta), "exec"),
                 {"__name__": "__main__", "__file__": str(ruta)})
        salida = buf.getvalue()
        ok, detalle = True, ""
    except Exception:  # noqa: BLE001
        ok = False
        salida = buf.getvalue()
        detalle = traceback.format_exc(limit=4)
    finally:
        os.chdir(cwd)

    if ok:
        lineas = [l for l in salida.splitlines() if l.strip()]
        print(f"  OK    {ruta.name:44} {len(codigo):2} celdas de código")
        for l in lineas[-4:]:
            print(f"        | {l[:96]}")
    else:
        print(f"  FALLA {ruta.name}")
        print("        " + detalle.replace("\n", "\n        ")[:1600])
    return ok


if __name__ == "__main__":
    objetivos = sorted(NOTEBOOKS.glob("*.ipynb"))
    if len(sys.argv) > 1:
        objetivos = [NOTEBOOKS / f for f in sys.argv[1:]]
    print(f"\nEjecutando {len(objetivos)} notebook(s) desde {RAIZ}\n")
    resultados = {n.name: ejecutar(n) for n in objetivos}
    rotos = [n for n, ok in resultados.items() if not ok]
    print(f"\n{'=' * 60}")
    print(f"{len(resultados) - len(rotos)}/{len(resultados)} notebooks ejecutan sin error")
    if rotos:
        print("FALLAN: " + ", ".join(rotos))
    print("=" * 60)
    sys.exit(1 if rotos else 0)
