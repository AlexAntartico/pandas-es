# Ruta Pandas · de cero a producción

Plan de aprendizaje de pandas en español, con 32 lecciones, un **workbook integrador
por lección** sobre casos reales, y un generador de datasets sucios multilingüe
(Turquía, EAU, Alemania, Suecia, Polonia, España) para practicar limpieza de texto.

Todo está pensado para **JupyterLab desde terminal en Linux**.

Notaras que las lecciones no estan completadas ni generadas, esto es a proposito. Este proyecto es el blueprint que puedes utilizar y customizar para agregar cualquier leccion especifica o enfoque que desees en `PLAN.md`.

Aparte de los 6 notebooks ya generados y los datasets que puedes ajustar con el seed, dependiendo del modelo usado, podras obtener distintos resultados.

---

## Arranque rápido

```bash
# 1. entorno
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. kernel de Jupyter apuntando a este venv
python -m ipykernel install --user --name pandas-es --display-name "Python (pandas-es)"

# 3. generar los datasets sucios
python generar_datasets_sucios.py

# 4. abrir JupyterLab en la raíz del proyecto
jupyter lab --notebook-dir=. --ServerApp.default_kernel_name=pandas-es
```

> Los notebooks asumen que el directorio de trabajo es la **raíz del proyecto**
> (`pandas-es/`), y por eso usan `datos/`, no `../datos/`. El helper
> `herramientas.cargar()` ya trae los parámetros correctos de cada fichero.

---

## Qué hay aquí

```
pandas-es/
├── PLAN.md                      el plan completo: 32 lecciones, 5 niveles
├── PROMPTS.md                   6 prompts listos para pegar en `mcode`
├── generar_datasets_sucios.py  genera los 8 datasets (determinista)
├── validar_limpieza.py          comprueba que tu pipeline no ha perdido datos
├── ejecutar_notebooks.py        ejecuta los notebooks y verifica que no fallan
├── requirements.txt
├── build/                       generador de los .ipynb de ejemplo
├── datos/                       los 8 datasets sucios  (se generan)
├── notebooks/
│   ├── herramientas.py          helpers: carga, normalización, exportación
│   ├── L01_cargar_csv_tsv.ipynb
│   ├── L05_groupby_cierre.ipynb
│   ├── L07_calidad_datos.ipynb
│   ├── L10_alfabetos_no_latinos.ipynb
│   ├── L14_series_temporales.ipynb
│   └── L21_visualizacion.ipynb
└── salida/                      los entregables que producen los workbooks
```

---

## Los dos entregables

**1. El plan de aprendizaje** → [`PLAN.md`](PLAN.md)

32 lecciones en 5 niveles (Cimientos, Limpieza, Análisis, Visualización,
Producción). Cada lección tiene: el concepto, manos a la obra, la trampa, y un
**workbook integrador** de caso real que produce un artefacto en disco. Recuerda que puedes modificarlos para agregar temas o pedirle al LLM que haga un enfoque en algun concepto o tema especifico. Ningun Notebook aparte los 6 ya generados va a ser igual.

**Nota** Al momento de realizar esta guia, estoy probando mcode, pero tu puedes usar cualquier herramienta que desees. Codex es mi go-to, y ultimamente Grok Build. Opencode con Deepseek y Kimi o deepinfra bajan mucho los costos.

**2. Los prompts para `mcode`** → [`PROMPTS.md`](PROMPTS.md)

6 prompts completos, cada uno autónomo:

| # | Prompt | Qué genera |
|---|---|---|
| 1 | Generador de datasets sucios | `generar_datasets_sucios.py` con los 8 ficheros |
| 2 | Generador de notebooks | los `.ipynb` de un rango de lecciones que le pidas |
| 3 | Revisión crítica | audita y **arregla** lo que el 2 ha generado |
| 4 | Alfabetos (caso especial) | la L10, con las trampas demostradas en código |
| 5 | Visualización | los notebooks de gráficos, con anti-patrones |
| 6 | Capstone | pipeline + tests + informe + recomendación |

Orden: **1 → ejecuta → 2 → 3**.

---

## Datasets incluidos

Los 8 ficheros simulan problemas reales, no casos inventados:

| Fichero | Caso real | Suciedad principal |
|---|---|---|
| `ventas_2024_este.csv` | export de ERP español | `;` + coma decimal + `latin-1` + `dd/mm/yyyy` |
| `ventas_2024_oeste.tsv` | el mismo ERP, otra región | TAB + punto decimal + fechas ISO + otro esquema |
| `clientes_crm.csv` | CRM comercial | duplicados, 6 alfabetos, mojibake, 2 espacios, tabs |
| `productos_catalogo.csv` | maestro de artículos | acentos, sufijos societarios, unidades, precios ×100 |
| `logistica_envios.csv` | API de paquetería | 3 husos + DST + estados en texto libre |
| `finanzas_conciliacion.csv` | extracto bancario | **5 formatos monetarios en la misma columna** |
| `rrhh_nominas.xlsx` | nóminas | columnas por año (para `melt`), importes como texto |
| `encuestas_satisfaccion.csv` | formulario online | Likert como texto, HTML entities, emojis |

Los nombres del CRM incluyen los casos trampa **reales**: `Ibrahim`/`İbrahim`/
`istanbul`, `Mueller`/`Müller`, `Straße`/`STRASSE`, `Soderberg`/`Söderberg`,
`Łukasz`/`Lukasz`, `Jürgen`/`Jurgen`, `Çağlayan`/`Caglayan`, `محمد`/`أحمد`/`أَحْمَد`/`Ahmad`.

---

## El caso de los alfabetos (L10)

Es la lección con más trampa del curso, y el ejecutor la verifica contra los datos:

```python
'ß'.casefold()   ->  'ss'    # casefold ALARGA la cadena
'İ'.lower()      ->  'i' + U+0307   # 1 carácter se vuelve 2
'I'.lower()      ->  'i'    # correcto en Unicode, INCORRECTO en turco
'ş' (U+015F) ≠ 'ș' (U+0219) ≠ 'ś' (U+015B)   # parecen iguales, no lo son
len('أَحْمَد') != len('أحمد')   # el tashkil no se ve pero cuenta
```

La clave canónica de `herramientas.py` **no destruye** el texto no latino: los
nombres árabes y griegos se conservan, porque `unidecode('محمد') == 'mhmd'` es una
pérdida de información, no una limpieza. Y el workbook te pide **medir la tasa de
falsos positivos** de la normalización, porque `Łukasz` y `Lukasz` sí se funden.

Debido a que en mi trabajo actual tengo que lidiar con alfabetos Cirilicos, Arabes y Caracteres presentes en Turco y lenguajes Europeos, el dataset se enfoca en tener estos para poder practicar el normalizarlos. Creanme que esto puede romper un pipeline completo o simplemente proveer KPIs incorrectos al negocio.

---

## Comprobaciones

```bash
python ejecutar_notebooks.py          # ejecuta los 6 notebooks y verifica
python validar_limpieza.py --crudo datos/ventas_2024_este.csv \
    --limpio salida/ventas_limpias.csv --dinero Importe --clave "ID Pedido"
# ventas_limpias.csv lo escribes tú (L13). El script sale con código 1 si
# pierdes filas, dinero, o la clave queda duplicada.
```

`ejecutar_notebooks.py` no necesita Jupyter: extrae las celdas de código y las
ejecuta como un script. Un `.ipynb` válido en formato pero con código roto no sirve
de nada, y esto lo comprueba.

---

## Exportación

Desde los notebooks, `herramientas` te da:

- `guardar_excel(df, ...)` → `.xlsx` con cabecera formateada, anchos y filtros
- `guardar_csv(df, ...)` → `.csv` con `utf-8-sig` (Excel en español no rompe tildes)
- `guardar_figura(fig, ...)` → **PNG** (pegar en slides), **SVG** (imprimir sin
  perder nitidez), **PDF** (el que exige casi todo proceso)
- `guardar_html(fig, ...)` → HTML autocontenido de una figura plotly

Para pasar un notebook a PDF:

```bash
jupyter nbconvert --to pdf notebooks/L05_groupby_cierre.ipynb
```
