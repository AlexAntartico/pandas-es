# Ruta Pandas — De cero a producción

Plan de aprendizaje en español. 32 lecciones agrupadas en 5 niveles, cada una con un
**workbook integrador** al final que replica un problema real de negocio/ingeniería.

Cada lección sigue el mismo contrato pedagógico:

1. **Concepto** — la idea, en 5-10 líneas, sin jerga innecesaria.
2. **Manos a la obra** — código mínimo, ejecutable, que se parece a lo que escribirás de verdad.
3. **Trampa** — el error que casi todos cometen con ese concepto.
4. **Workbook integrador** — un ejercicio de mundo real sobre datasets del proyecto.

Regla de oro del curso: **nunca hay una lección sin un dataset real en la carpeta `datos/`.**

---

## Nivel 0 — Cimientos (lecciones 1-6)

### L01 · Abrir un CSV y un TSV
- **Concepto:** `pd.read_csv` y `read_table`. El separador es el problema número uno del mundo real.
- **Manos a la obra:** `read_csv` con `sep=`, `header=`, `nrows`, `usecols`, `encoding`, `decimal=`, `thousands=`.
- **Trampa:** asumir `sep=","`. En España/Latinoamérica el 60% de los CSV exportados de ERPs usan `;` con decimal `,`.
- **Workbook:** *Auditoría de carga.* Cargar 6 archivos (`,` `;` `\t` `|` decimal americano/europeo) y reportar para cada uno: filas, columnas, delimitador real, encoding y 3 anomalías. Entregar un `.csv` con el diagnóstico.

### L02 · El DataFrame: anatomía y primeras exploraciones
- **Concepto:** índice, columnas, ejes, dtypes, `.shape`. Por qué un DataFrame no es una tabla de Excel.
- **Manos a la obra:** `head`, `tail`, `info`, `describe`, `dtypes`, `value_counts`, `memory_usage`.
- **Trampa:** `df.describe()` sobre columnas con texto No hace nada útil y no avisa. Mejor `describe(include="all")`.
- **Workbook:** *Ficha técnica de dataset.* Escribir una función `ficha(df)` que devuelva nº filas/cols, tipos, % nulos, duplicados, cardinalidad por columna y memoria, y aplícala a los 6 archivos de L01.

### L03 · Seleccionar datos: loc, iloc y máscaras
- **Concepto:** tres formas de Indexar. `loc` por etiquetas, `iloc` por posición, máscara booleana por contenido.
- **Manos a la obra:** `df.loc[cond, cols]`, `df.iloc[0:10, 2:5]`, `df[df.ventas > 1000]`, `query()`.
- **Trampa:** encadenar `df[df.a > 1]["b"].sum()` funciona, pero `df["b"][df.a > 1]` ya cambió de semántica en pandas 3. Usa siempre `.loc`.
- **Workbook:** *Consultas de negocio.* Responder 8 preguntas (top cliente, ventas Q1, pedidos con más de 3 líneas, ticket medio por región) usando obligatoriamente `.loc`, `.iloc`, máscara y `query` — una pregunta por cada método.

### L04 · Columnas: crear, transformar, renombrar
- **Concepto:** el 80% del trabajo de datos es derivar columnas. `assign` encadena sin mutar el original.
- **Manos a la obra:** `assign`, `astype`, `str` accessors, `np.where`, `np.select`, `rename`, `drop`.
- **Trampa:** `df["col"] = ...` muta en el sitio; `df.assign(...)` devuelve copia. En un pipeline importa cuál usas.
- **Workbook:** *Ingeniería de features.* A partir de un CSV de pedidos, crear: margen, %, descuento neto, flag de pedido grande, categoría de ticket, y renombrar todo a español con unidades en el nombre (`importe_eur`).

### L05 · aggregating con groupby
- **Concepto:** split-apply-combine. La operación más usada en análisis de datos y la que más errores da.
- **Manos a la obra:** `groupby().agg()`, `agg` con dict, `transform`, `size` vs `count`, `nunique`, `sort_values`.
- **Trampa:** `size` cuenta filas incluyendo NaN; `count` los excluye. En un conteo de clientes, esto cambia el número.
- **Workbook:** *Reporte mensual.* Generar el cierre por mes × región × categoría: ventas, margen, nº pedidos, ticket medio, % sobre el total del mes. Entregar en Excel con formato.

### L06 · Uniones: merge, join y concat
- **Concepto:** cómo se combinan tablas y por qué `merge` puede multiplicar filas silenciosamente.
- **Manos a la obra:** `merge` (how: inner/left/right/outer), `indicator`, `validate`, `concat`, `join`.
- **Trampa:** sin `validate="m:1"`, un `left` join con duplicados en la derecha **duplica filas** y ni te avisa. En facturación esto son millones falsos.
- **Workbook:** *Enriquecimiento de pedidos.* Unir cabecera de pedidos con líneas y con clientes, detectar y reportar el nº de filas perdidas y duplicadas por cada `how`, y entregar el dataset final con `validate`.

---

## Nivel 1 — Limpieza (lecciones 7-13)

### L07 · Detectar problemas: nulls, duplicados y tipos
- **Concepto:** perfilado de calidad. Antes de limpiar, medir.
- **Manos a la obra:** `isna().sum()`, `duplicated`, `value_counts(dropna=False)`, `dtypes`, `infer_objects`.
- **Trampa:** los "falsos nulos": `"NA"`, `"N/A"`, `""`, `"-"`, `"null"`, `"SIN DATO"`, `0` en columnas de edad. `isna` no los ve.
- **Workbook:** *Informe de calidad.* Función que devuelva, por columna: % nulos reales, % falsos nulos, % duplicados de fila, nº de valores inconsistentes. Aplicar a los 6 archivos sucios.

### L08 · Limpiar tipos: fechas, números, booleanos
- **Concepto:** la causa nº1 de `SettingWithCopyWarning` y de errores de cálculo.
- **Manos a la obra:** `to_numeric(errors="coerce")`, `to_datetime(format=)`, `pd.to_timedelta`, `astype("category")`.
- **Trampa:** `pd.to_datetime` adivina el formato y con fechas `01/02/2024` (ambiguas dd/mm vs mm/dd) falla en silencio. **Siempre pasa `format=` y `dayfirst=`.**
- **Workbook:** *Normalización de tipos.* Un CSV con 8 columnas "de texto" (fechas, importes, booleanos, códigos con ceros a la izquierda) → convertirlas todas, reportar cuántas filas se perdieron por coerción y justificar cada decisión.

### L09 · Texto sucio: espacios, mayúsculas, acentos y uniones
- **Concepto:** normalización de cadenas. La lección que más horas ahorra en limpieza de datos reales.
- **Manos a la obra:** `str.strip`, `str.lower`, `str.replace(regex)`, `str.normalize("NFKD")`, `str.contains`, `str.extract(regex)`.
- **Trampa:** normalizar a mayúsculas y quitar acentos **destruye la distinción entre personas** (`José`/`Jose`, `Müller`/`Muller` son la misma persona, `Söder`/`Soder` casi siempre también). Decide según el caso de uso.
- **Workbook:** *Catálogo de productos.* El maestro `productos_catalogo.csv` (~4.000 referencias) con espacios dobles, tabs, acentos inconsistentes, mayúsculas mezcladas y sufijos (`S.A.`, `S.L.`, `SA`). Limpiar y hacer join contra el maestro oficial, midiendo el % de match antes y después.

### L10 · Alfabetos no latinos

- **Concepto:** por qué `"İ".lower()` no te da `"i"`, por qué `"ß".casefold()` **cambia la longitud** de la cadena, y por qué una comparación ingenua fusiona personas distintas.
- **Manos a la obra:** `unicodedata.normalize("NFKD"/"NFKC")`, `casefold` vs `lower` vs `upper`, detección de script con `regex` (`\p{Script=Arabic}`, `\p{Script=Cyrillic}`), transliteración con `unidecode`, y una clave canónica en varias capas.
- **Trampa (medida, no de memoria).** Ejecuta esto antes de creer cualquiera de estas afirmaciones:

  | Entrada | `len` | `.lower()` | `len(lower)` | `.casefold()` | `len(casefold)` |
  |---|---|---|---|---|---|
  | `I` | 1 | `i` | 1 | `i` | 1 |
  | `İ` | 1 | `i` + U+0307 | **2** | `i` + U+0307 | **2** |
  | `ı` | 1 | `ı` | 1 | `ı` | 1 |
  | `ß` | 1 | `ß` | 1 | `ss` | **2** |
  | `ẞ` | 1 | `ß` | 1 | `ss` | **2** |
  | `ø` | 1 | `ø` | 1 | `ø` | 1 |
  | `ł` | 1 | `ł` | 1 | `ł` | 1 |

  Conclusiones que salen de la tabla, y que **sí** importan:
  - `casefold` puede **alargar** la cadena (`ß`→`ss`). Cualquier código que asuma "una letra = un carácter", o que compare longitudes, se rompe.
  - `lower` **no** es `casefold`. Para hacer join de nombres, `casefold`; para formatear salida, `lower`.
  - `İ`.lower() da **2 caracteres**, uno de ellos combinante. Si haces slicing por índice, estás comparando basura.
  - `ł`, `ø`, `đ`, `þ`, `æ` **no tienen equivalente ASCII** y `casefold` no los toca. Si un sistema transliteró y otro no, necesitas `unidecode` como capa explícita.
  - El rumano `ș` (U+0219, *below*), el **`ş` turco** (U+015F, *cedilla*) y el polaco `Ś` son caracteres **distintos** de apariencia casi idéntica. Se cuelan solos en catálogos con ruido.
- **Trampa (turco).** `I` (U+0049), `ı` (U+0131) e `İ` (U+0130) son tres caracteres distintos con el mismo sonido. En un sistema turco, quien teclea `I` produce `ı` al escribir su nombre en minúscula. El `str.lower()` de Python es **locale-independent**: `"I".lower()` da `"i"`, que es lo correcto según Unicode, pero **incorrecto** para el turco. Consecuencia práctica: `"Ibrahim"` y `"ıbrahim"` no hacen match con `==` ni con un `merge` por clave, aunque para un humano sean el mismo nombre. La solución no es "arreglar `lower`", es **generar una clave canónica** que aplique transliteración además de `casefold`.
- **Trampa (árabe).** El texto es RTL (marcas U+200F/U+200E) y admite *tashkil* (marcas U+064B-0652), que se **suman** a la longitud de la cadena sin verse: `"أحمد"` y `"أَحْمَد"` son el mismo nombre con distinta longitud. Además hay variantes de alef (`أ إ آ ا`), `ة` vs `ه`, y `ى` vs `ي`. Esto rompe los joins (si una parte viene transliterada y otra no), el slicing por índice, y cualquier `len()` usado como validación. **Nunca** valides texto árabe con `len()`.
- **Trampa (europeos).** Además de `ß/ẞ`: `ł/Ł` (polaco), `đ/Đ` (croata), `þ/Þ` y `ð/Ð` (islandés), `æ/Æ` y `ø/Ø` (danés), `ż`, `ź`, `ć`, `ń`, `ś`. Ninguno tiene equivalente ASCII estándar, y `unidecode` los convierte a aproximaciones (`ł`→`l`, `ø`→`o`, `đ`→`d`, `ß`→`ss`). **La aproximación no es reversible**: si dos personas distintas se llaman `Łukasz` y `Lukasz`, un join por clave transliterada las fusiona. Eso es un falso positivo, y por eso el workbook te pide medirlos.
- **Workbook:** *Normalización multilingüe.* Dataset de clientes de una empresa con operaciones en **Turquía, EAU, Alemania, Suecia, Polonia y España**. Cada cliente aparece 2-3 veces en distinto alfabeto u ortografía. Objetivo en tres capas:
  1. Construir una `clave_canonica` (casefold → NFKD quita diacríticos → unidecode quita lo no-ASCII → colapsa espacios).
  2. Colapsar los duplicados por esa clave.
  3. **Medir y entregar el coste de esa decisión:** una muestra de fusiones para auditar a mano, y la **tasa de falsos positivos** estimada cruzando con país + email. Una solución que funde el 100% y acierta el 40% no es una solución, es un problema nuevo.

### L11 · Duplicados y claves únicas
- **Concepto:** qué es un duplicado real vs un duplicado de negocio.
- **Manos a la obra:** `duplicated(subset=)`, `drop_duplicates(keep=)`, `duplicated` en panel data, claves compuestas.
- **Trampa:** un cliente con 3 pedidos **no** es un duplicado de cliente. `drop_duplicates()` sin `subset` solo quita filas idénticas en todas las columnas. Lo que destruye el histórico de líneas es `drop_duplicates(subset="pedido")`.
- **Workbook:** *Consolidación de contactos.* Fusionar 4 exports del CRM (distintos sistemas, distintos formatos) en una tabla de contactos únicos, con estrategia de "ganador" por campo y un log de qué se descartó y por qué.

### L12 · Outliers y valores imposibles
- **Concepto:** distinguir error de captura de evento real.
- **Manos a la obra:** IQR, z-score, winsorizing, `clip`, rangos por dominio.
- **Trampa:** un pedido de 250.000 € puede ser legítimo (corporativo) y un IQR lo matará. Los outliers **casi siempre son el dato interesante**, no el error.
- **Workbook:** *Control de calidad de precios.* Catálogo con precios 100× exagerados por error de carga (p. ej. `19.99` → `1999.00`), precios por debajo de coste y una moneda mixta. Detectar con reglas de negocio, no solo estadística.

### L13 · El pipeline de limpieza completo
- **Concepto:** encadenar transformaciones de forma reproducible y auditable.
- **Manos a la obra:** funciones puras encadenadas con `assign`, un `dict` de reglas, `pipe`, y tests smoke.
- **Trampa:** un `for` de 40 líneas de `df[col] = ...` no es reproducible ni testeable. Divide en funciones.
- **Workbook:** **ENTREGA FINAL NIVEL 1.** `limpiar_ventas.py` que tome el CSV más sucio del proyecto, aplique **todas** las lecciones 7-12, y produzca `ventas_limpias.parquet` + un `reporte_calidad.html` con las métricas antes/después.

---

## Nivel 2 — Análisis (lecciones 14-20)

### L14 · Series temporales
- **Concepto:** índice temporal, resampleo, ventanas móviles, estacionalidad.
- **Manos a la obra:** `set_index`, `resample("ME")`, `rolling(7)`, `expanding`, `shift`, `pct_change`.
- **Trampa:** `resample("M")` en pandas <2.2 vs `"ME"` en 2.2+. En pandas 3 `"M"` está deprecado. Usa siempre las nuevas (`ME`, `QE`, `YE`, `W`).
- **Workbook:** *Demanda y stock.* Serie diaria de coste de envío de 2024 (el fichero de logística cubre un año, no dos): media móvil, tendencia y detección de anomalías sobre las diferencias. Exportar a CSV y a un gráfico.

### L15 · groupby avanzado y ventanas
- **Concepto:** groupby con transformaciones que conservan la forma original, rolling por grupo.
- **Manos a la obra:** `transform`, `groupby().rolling()`, `shift` por grupo, `rank` por grupo, top-N por grupo.
- **Trampa:** `df.groupby("a")["b"].rolling(3)` devuelve un índice jerárquico raro. Hay que `reset_index` o usar `groupby(...).transform(lambda...)` con cuidado de rendimiento.
- **Workbook:** *Ranking por cliente.* Para cada cliente: nº de pedidos, ticket medio, varianza, posición dentro de su segmento, y "es su mayor compra histórica" como booleano. Todo con groupby, sin loops.

### L16 · Reescribir datos: melt, pivot, crosstab
- **Concepto:** pasar de ancho a largo y volver. Formato tidy.
- **Manos a la obra:** `melt`, `pivot`, `pivot_table`, `stack`/`unstack`, `crosstab`, `get_dummies`.
- **Trampa:** `pivot` falla si hay duplicados en la combinación clave; `pivot_table` los agrega silenciosamente. Usa `pivot` cuando quieres que **falle**.
- **Workbook:** *InformeWide→Tidy.* Una tabla con 12 columnas `importe_2023_01`...`importe_2023_12` que hay que pasar a formato largo, agregar y devolver a ancho para el reporting.

### L17 · Consultas estilo SQL
- **Concepto:** `query`, `eval`, y el puente `read_sql` / `to_sql`.
- **Manos a la obra:** sintaxis de `query()` con `@variables`, `pd.read_sql`, `to_sql` con chunksize.
- **Trampa:** `df.query("a > @media")` requiere que `media` esté en el scope. Error silencioso → `NameError` en vez de resultado vacío.
- **Workbook:** *Traducción SQL→pandas.* Reescribir 8 consultas SQL de un reporting real usando `query` y `merge`, y comparar tiempo de ejecución.

### L18 · Fechas, zonas horarias y negocio
- **Concepto:** fechas de negocio vs fechas de sistema. Dst, UTC, fines de semana.
- **Manos a la obra:** `tz_localize` vs `tz_convert`, `dt` accessors, `BusinessDay`, `offsets`.
- **Trampa:** `tz_localize` en un timestamp ya consciente lanza error; `tz_convert` en uno naive también. Y un día de DST puede tener 23 o 25 horas.
- **Workbook:** *Agenda de citas.* Sistema de reservas con horas en 3 husos distintos, cruza los DST de marzo y octubre, y calcula disponibilidad real vs nominal.

### L19 · Análisis exploratorio: guía completa
- **Concepto:** método. Hipótesis, no gráficos.
- **Manos a la obra:** el flujo perfilo → calidad → distribución → relación → outlier → segmentación.
- **Trampa:** la gráfica de 40 subplots no es un análisis, es un postpone.
- **Workbook:** **ENTREGA FINAL NIVEL 2.** EDA completo del dataset de clientes: 6 hipótesis, cada una con su pregunta, su query, su resultado y su conclusión por escrito.

### L20 · Case study: análisis de cohortes y retención
- **Concepto:** caso completo que junta casi todo lo aprendido.
- **Manos a la obra:** cohortes mensuales, retención, churn, LTV.
- **Trampa:** definir la cohorte por la fecha del **primer** evento, no por la de cada evento. Si no, la retención da >100%.
- **Workbook:** **ENTREGA FINAL NIVEL 2.** Análisis de cohortes de una app, con heatmap de retención, curva LTV y segmentación de churners.

---

## Nivel 3 — Visualización (lecciones 21-26)

### L21 · matplotlib: el control total
- **Concepto:** la librería base. Figuras, ejes, capas.
- **Manos a la obra:** `plt.subplots`, `ax.` methods, figuras de múltiples paneles, `figsize`/`dpi`/`tight_layout`.
- **Trampa:** el 95% del tiempo perdido con matplotlib es la API dual `plt.` vs `ax.`. Usa el **método OO**: crea `fig, ax` y llama a `ax.*`. Nunca `plt.*` después.
- **Workbook:** *Dashboard de KPI.* Grid 2×2 con ventas mensuales, top productos, distribución de tickets, y mapa de calor. Exportar a PNG de calidad publicación.

### L22 · seaborn: statistical plots
- **Concepto:** lo que matplotlib hace largo.
- **Manos a la obra:** `relplot`, `catplot`, `displot`, `histplot`, `boxplot`, `violinplot`, `pairplot`, `lmplot`, `heatmap`, `FacetGrid`.
- **Trampa:** `pairplot` sobre 50 columnas y 500k filas = cuelgue total. Submuestrea.
- **Workbook:** *Análisis multivariante.* Reemplazar 6 gráficos de matplotlib por 6 seaborn plots equivalents, con paleta consistente y facet por segmento.

### L23 · Paletas, estilo y consistencia visual
- **Concepto:** coherencia. Un dashboard se ve profesional por consistencia, no por sofisticación.
- **Manos a la obra:** paletas (viridis, cividis, Okabe-Ito), mapas de color secuenciales vs divergentes vs categóricos, `set_theme`, rcParams, style sheets.
- **Trampa:** usar una paleta **divergente** (rojo-azul) para datos que van de 0 a 100. Redundancia de color. Secuencial para eso.
- **Workbook:** *Sistema de diseño.* Definir un tema (paleta, tipografía, tamaños) y aplicar a 6 gráficos distintos. Entregar el tema como archivo `.mplstyle` o dict de rcParams.

### L24 · Visualización de experto: anatomía de un buen gráfico
- **Concepto:** qué separa un gráfico de un meme corporativo.
- **Manos a la obra:** quitar chartjunk, ordenar por valor, anotar directamente, unidades en el título, fuente citada, elegir línea vs barra según la pregunta.
- **Trampa:** 13 colores, 3 ejes, gradiente, sombra 3D y leyenda de 20 entradas. Cero información.
- **Workbook:** **Rediseño.** Te dan 3 gráficos horribles (ruidosos, 3D, truncado en Y). Rehacerlos aplicando las 8 reglas. Documentar antes/después.

### L25 · plotly: interactividad
- **Concepto:** gráficos que se exploran, se embeben y se comparten.
- **Manos a la obra:** `px.bar/line/scatter`, facet, hover, `plotly.express` + `graph_objects`, `update_layout`, templates.
- **Trampa:** 200.000 puntos en un `Scatter` sin `WebGL` = navegador muerto. Usa `scattergl`.
- **Workbook:** *Reporte exploratorio.* Figura plotly con dropdown de métrica, filtro de región por clic, y export a HTML autocontenido.

### L26 · Exportación: del notebook al entregable
- **Concepto:** cómo convertir tus gráficos en algo que se manda y se archiva.
- **Manos a la obra:** `savefig` (png/svg/pdf), `fig.write_html`, `nbconvert --to pdf/slides`, `kaleido` para plotly, exportar DataFrames a Excel con formato.
- **Trampa:** `savefig` antes de `plt.show()` en `%matplotlib inline` **no falla**, pero en un script sí. Y el PDF exportado pierde los gráficos interactivos.
- **Workbook:** **ENTREGA FINAL NIVEL 3.** Notebook que se convierte en PDF de 3 páginas con todos los gráficos, y en un HTML con las interactivas.

---

## Nivel 4 — Producción (lecciones 27-32)

### L27 · SQL, pandas y Spark
- **Concepto:** no todo se resuelve en memoria.
- **Manos a la obra:** `read_sql` con chunksize, `to_sql` con if_exists, lógica de pushdown, sampling.
- **Trampa:** traer 2.000.000 filas para hacer un `groupby` que la base de datos hacía en 0.4s. **Filtra y agrega en la fuente.**
- **Workbook:** *Migración de reporte.* Un reporte mensual de 90M filas que tardaba 20 min en SQL. Reimplementar en pandas optimizado y comparar tiempos.

### L28 · Eficiencia y memoria
- **Concepto:** reducir el footprint.
- **Manos a la obra:** `memory_usage(deep=True)`, downcasting de dtypes, `category`, `parquet` vs `csv`, fechas como datetime64, `usecols` + `dtype`.
- **Trampa:** un CSV de 8 GB con una columna de IDs como texto puede bajar a 400 MB con parquet + categoricals. Pero **parquet no preserva el orden de filas** si no lo pides.
- **Workbook:** *Optimización.* Un dataset de 2M × 30. Reducir memoria >60%, mantener exactamente los mismos agregados, y documentar el antes/después. Prohibido usar `float64` donde `float32` basta.

### L29 · Testing de código de datos
- **Concepto:** un pipeline sin tests es un script que un día te traiciona.
- **Manos a la obra:** pytest para transformaciones, `pandas.testing.assert_frame_equal`, fixtures pequeñas, checks de esquema.
- **Trampa:** testear el valor de una celda de notebook. Testea la **función**, no el resultado cacheado.
- **Workbook:** *Tests del pipeline.* Escribir 10 tests para tu `limpiar_ventas.py` de L13: nulos, tipos, rangos, unicidad, invariantes de totales.

### L30 · Automatización de notebooks
- **Concepto:** los notebooks no son software, son documentos. El código va a `.py`.
- **Manos a la obra:** Cell magic vs código, `%%timeit`, `nbconvert --execute`, `papermill` para notebooks parametrizados, `ruff`.
- **Trampa:** lógica de negocio escondida en celdas markdown o en outputs que se borran. Si no se puede re-ejecutar, no es reproducible.
- **Workbook:** **ENTREGA FINAL NIVEL 4.** Convertir tu notebook del nivel 3 en un módulo `.py` testeado + un `.ipynb` que solo lo llama. Parametrizar con `papermill`.

### L31 · Concurrencia y volumen masivo
- **Concepto:** cuando `read_csv` se queda corto.
- **Manos a la obra:** `chunksize` + iterador, `pyarrow` + `polars` para scanning, Dask básico.
- **Trampa:** concatenar 500 chunks con `pd.concat` de 500k filas cada uno = explosión de memoria. Agrega chunk a chunk con `reduce`.
- **Workbook:** *Procesamiento por lotes.* Procesar 40 archivos de 300 MB cada uno con memoria **constante** (constreint: <2 GB RAM) y agregar los resultados.

### L32 · Proyecto capstone: decisión con datos
- **Concepto:** todo lo anterior sirve a una decisión.
- **Manos a la obra:** pregunta → datos → limpieza → análisis → visualización → **recomendación**.
- **Trampa:** el informe de 40 páginas sin recomendación. El stakeholder no pidió tu análisis, pidió qué hacer.
- **Workbook:** **PROYECTO FINAL.** Conjunto de 4 datasets sucios de una empresa de retail. Entregar: pipeline reproducible, informe PDF con visualizaciones, tests, y **una recomendación ejecutiva de 1 página**.

---

## Mapa de desbloqueo

```
Nivel 0 (1-6) → saber leer y escribir tablas [base]
Nivel 1 (7-13) → saber limpiar datos reales [productividad]
Nivel 2 (14-20) → saber analizar y responder preguntas [insight]
Nivel 3 (21-26) → saber comunicar visualmente [impacto]
Nivel 4 (27-32) → saber llevar a producción [escala]
```

**Tiempo estimado:** 8-12 semanas a 6-8h/semana. Los niveles 0-1 son el 60% del valor.

---

## Datasets del proyecto

Todos generados por `generar_datasets_sucios.py` (ver `PROMPTS.md` para regenerarlos):

| Archivo | Caso real | Suciedad principal |
|---|---|---|
| `ventas_2024_este.csv` | Export de ERP | `;` decimal `,` euros, fechas dd/mm |
| `ventas_2024_oeste.tsv` | Mismo ERP, otra región | tab, ISO dates, encoding utf-8 |
| `clientes_crm.csv` | CRM comercial | duplicados, mojibake, multi-alfabeto |
| `productos_catalogo.csv` | Maestro de artículos | acentos, unidades, sufijos societarios, dups |
| `logistica_envios.csv` | API de paquetería | 3 husos, DST, nulos, estados libres |
| `rrhh_nominas.xlsx` | Nóminas | negativos, currencies, columnas anidadas |
| `finanzas_conciliacion.csv` | Extracto bancario | format mixto, 2 decimales vs 0, ref duplicadas |
| `encuestas_satisfaccion.csv` | SurveyMonkey | Likert como texto, HTML entities, emojis |

---

## Cómo se conecta con los prompts

1. Copia el **PROMPT MAESTRO** de `PROMPTS.md` a `mcode` en tu terminal.
2. `mcode` genera `generar_datasets_sucios.py` → ejecutas → tienes `datos/`.
3. Por cada lección: el prompt correspondiente de `PROMPTS.md` genera el notebook.
4. Los **workbooks integradores** están especificados arriba; `mcode` los implementa con
 validación de que el código corre y produce un artefacto.
