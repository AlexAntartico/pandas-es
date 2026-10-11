# PROMPTS para `mcode`

Cada bloque es un prompt **completo y autónomo**. Cópialo tal cual en tu terminal
donde corres `mcode`. No necesitas contexto previo: cada prompt incluye todo lo que
`mcode` necesita saber.

Orden recomendado de ejecución:

```
1. PROMPT 1  → genera generar_datasets_sucios.py
2. ejecuta   → python generar_datasets_sucios.py
3. PROMPT 2  → genera los 32 notebooks (o el rango que le pidas)
4. PROMPT 3  → audita y corrige lo generado
```

Tip: si quieres solo algunas lecciones, cambia la línea "genera las lecciones X a Y".

---
---

# PROMPT 1 — Generador de datasets sucios (con alfabetos reales)

```
Crea un archivo llamado `generar_datasets_sucios.py` en el directorio actual.

Es un generador de datasets "sucios" para un curso de pandas, escrito en español en los
comentarios y en los nombres de los ficheros. Debe ser un script autónomo, ejecutable con
`python generar_datasets_sucios.py`, que use SOLO pandas + numpy + stdlib, que sea
DETERMINISTA (semilla fija, `--seed` por defecto 42, mismo resultado siempre) y que
escriba 8 ficheros en una carpeta `datos/`.

Cada dataset debe simular un caso REAL de empresa, no un caso inventado:

1. `ventas_2024_este.csv` — export de un ERP español. Separador `;`, coma decimal,
   encoding `latin-1`, fechas en `dd/mm/yyyy`, cabeceras con espacios y acentos
   ("ID Pedido", "Fecha Pedido", "Precio Unitario"). Columna "Descuento %" con un 5% de
   celdas literalmente vacías. ~12000 filas con columnas: ID Pedido, Fecha Pedido,
   ID Cliente, Region, Categoria, Canal, Metodo Pago, Unidades, Precio Unitario, Importe,
   Descuento %.

2. `ventas_2024_oeste.tsv` — el MISMO ERP, otra región, pero otro formato: separador TAB,
   punto decimal, fechas ISO `YYYY-MM-DD`, cabeceras en
   inglés (order_id, order_date, customer_id, region, category, qty, unit_price, total,
   currency), encoding utf-8. ~9000 filas. Esto obliga a unificar dos esquemas distintos.

3. `clientes_crm.csv` — CRM comercial con el caso más interesante de todos. ~6000 clientes
   base, encoding `utf-8-sig` (con BOM, como exporta Excel). Columnas: cliente_id, nombre,
   pais, email, telefono, alta, segmento, ciudad, saldo. Requisitos:
   - El 35% de los clientes aparece una segunda vez con el MISMO nombre escrito de otra
     forma: en mayúsculas, en minúsculas, sin acentos (NFD quitando diacríticos), con `ß`
     convertido a `ss`, sin espacios, o con transliteraciónGermana (`Müller`→`Mueller`).
   - ~400 filas duplicadas EXACTAS (mismo cliente importado dos veces).
   - Un 10% de nombres con espacios dobles, un 3% con tabulador inicial.
   - Nombres en 6 países con problemas reales de alfabeto. Incluye una lista explícita de
     casos trampa que DEBEN aparecer: `Ibrahim` / `İbrahim` / `istanbul` / `IĞDIR`,
     `Mueller` / `Müller`, `Straße` / `STRASSE`, `Soderberg` / `Söderberg`,
     `Łukasz` / `Lukasz`, `Jürgen` / `Jurgen`, `Çağlayan` / `Caglayan`,
     `Đorđe` / `Dorđe`, y en árabe: `محمد`, `أحمد`, `أَحْمَد` (con tashkil), `Ahmad`,
     `Al-Farsi`, `Muḥammad`.
   - `saldo` como texto con coma decimal. `telefono` con 3% de vacíos.
   - Mezcla de países: ES (40%), TR (20%), AE (12%), DE (12%), SE (8%), PL (8%).

4. `productos_catalogo.csv` — maestro de artículos. ~4000 filas: sku, descripcion, precio
   (texto con coma), unidad_medida, familia, stock, activo. Suciedad:
   - ~45 descripciones base repetidas con variantes: con/sin acento, con/sin sufijo
     societario (" S.A.", " S.L.", " SA", " S.L.U.", " GmbH", " A.S.", " AB",
     " Sp. z o.o."), con la medida pegada ("500g", "500 g", "500G") o separada.
   - `unidad_medida` mezclando "ud", "UND", "unidad", "unidades", "UDS", "pz", "piece".
   - `activo` mezclando "S", "N", "si", "no", "Sí", "No", "1", "0" y los booleanos
     True/False (en el CSV salen como el texto True y False).
   - Un 10% de precios multiplicados por 100 (error de carga real: 19.99 → 1999.00).
   - 200 precios con 3 decimales (punto) y otros 200 sin decimales. El resto usa coma.

5. `logistica_envios.csv` — API de paquetería. ~8000 envíos: envio_id, pedido_id,
   pais_origen, huso_origen, fecha_envio_local, fecha_envio_utc, peso_kg, coste_envio,
   estado, transportista.
   - 3 husos horarios: Europe/Madrid (+1), Europe/Istanbul (+3), Asia/Dubai (+4).
   - `fecha_envio_local` mezcla dos formatos ISO: "2024-03-15T09:30:00" y
     "2024-03-15 09:30:00", y está en hora local. `fecha_envio_utc` es esa hora
     MENOS el offset (no más). Madrid es UTC+1 en invierno y UTC+2 entre el
     31 de marzo de 2024 a las 02:00 y el 27 de octubre a las 03:00. Estambul es
     UTC+3 todo el año y Dubái UTC+4. Siembra envíos en esos dos domingos.
   - IMPORTANTE: incluye envíos que caen en el cambio de hora de verano (último domingo
     de marzo y de octubre de 2024) para que la conversión de huso sea un problema real.
   - `estado` es texto libre con variantes: "Pendiente"/"pendiente"/"PENDIENTE",
     "Entregado"/"entregado"/"Entregado " (con espacio final), "En tránsito"/"En transito",
     más "Devuelto", "Perdido", "En reparto", "Retrasado", "En espera".
   - 3% de `peso_kg` realmente nulos (NaN, no "").
   - `peso_kg` y `coste_envio` como texto con coma decimal.

6. `finanzas_conciliacion.csv` — extracto bancario. ~6000 movimientos, separador `;`,
   encoding `latin-1`. Columnas: fecha_operacion, concepto, importe, saldo, referencia,
   conciliado.
   - LA PIEZA CENTRAL: la columna `importe` mezcla 5 formatos en la MISMA columna:
     (a) europeo "1.234,56" (con punto de miles de verdad: los importes tienen que
     pasar de 1000, si no el punto no sale), (b) americano "1234.56", (c) con
     separador de miles americano "1,234.56", (d) con moneda "EUR -1234.56"
     conservando el signo, (e) negativos entre paréntesis "(1234.56)" que significan
     -1234.56. Reparte aproximadamente 40/30/15/10/5.
   - Las referencias nacen únicas. Luego el 8% se empareja: cada referencia
     repetida la comparten dos movimientos, no cientos.
   - `fecha_operacion` mezcla `dd/mm/yyyy` y `YYYY-MM-DD` en la misma columna.
   - `concepto` en MAYÚSCULAS a veces, con y sin tilde ("DOMICILIACION", "Devolucion").
   - 8% de `referencia` repetida (dos movimientos con la misma referencia: no son
     duplicados, son movimientos distintos que hay que conciliar).
   - `conciliado` con "S", "N", "", "sí", "no".

7. `rrhh_nominas.xlsx` — nóminas, ~800 empleados, con el índice puesto en la columna
   `empleado_id` (usa `set_index` antes de `to_excel`). Columnas: nombre, pais,
   departamento, salario_base, plus_2022, plus_2023, plus_2024, bajas_2024.
   Nombres Europeos, turco, polacos y árabes. Todos los importes como texto con coma
   decimal. Sheet llamada "nominas". La estructura plus_2022/plus_2023/plus_2024 está
   pensada para que el alumno tenga que hacer `melt` en una lección posterior.

8. `encuestas_satisfaccion.csv` — ~2500 respuestas: respuesta_id, enviado, satisfaccion,
   velocidad_envio, calidad_producto, recomendaria, comentario.
   - Las columnas Likert mezclan etiquetas ("Muy mal", "Mal", "Normal", "Bien", "Muy bien")
     con números ("5", "4", "3", "2", "1") y con nulos ("ns/nc", "N/S", "-").
   - `recomendaria` con "Sí", "si", "No", "no", "Quizás", "1", "0" y celdas vacías.
   - `comentario` con HTML entities sin limpiar ("&amp;", "&lt;excelente&gt;"), emojis
     ("Llegó tarde 😞", "Excelente servicio 👍"), acentos, y un "NN/NN" de no respuesta.

REQUISITOS TÉCNICOS:
- Nada de faker ni de dependencias externas: solo pandas, numpy, random, unicodedata,
  datetime, argparse, pathlib.
- Un módulo con los catálogos (nombres, apellidos, ciudades por país) arriba, bien
  comentado, para que sea fácil de ampliar.
- Funciones separadas por dataset (`ventas_este()`, `clientes_crm()`, etc.) y una
  `guardar_todo(out, seed)` que coordina. Cada una debe poder testearse por separado.
- MANEJO DE TIPOS: estás sobre pandas 3.x, donde las columnas de texto usan dtype `str`
  estricto. NO asignes enteros ni NaN floats sobre una columna de texto creada con `""`
  (lanza TypeError). Convierte con `.astype(str)` o crea la columna con dtype `object`.
- MANEJO DE FECHAS: `timedelta()` NO acepta `np.int64`. Pasa siempre `int(...)` o `float(...)`.
- Al final, imprime una tabla con el nombre de cada fichero y su tamaño en KB.
- Al final, imprime también un pequeño informe por fichero indicando: nº de filas, nº de
  columnas, delimitador, encoding y las 3 anomalías principales que has sembrado. Esto
  sirve como Expected Answer para que el alumno sepa qué debería encontrar.

Escribe el archivo con buenos comentarios en español explicando el CASO REAL que simula
cada dataset, no sólo la mecánica. Ejecuta el script y comprueba que genera los 8 ficheros
sin errores. Si algo falla, arréglalo hasta que funcione.
```

---
---

# PROMPT 2 — Generar los notebooks del curso

```
Voy a darte el plan de un curso de pandas. Está en el archivo `PLAN.md` de este directorio.
Léelo entero primero.

Quiero que generes los notebooks .ipynb de las lecciones 1 a 6 (las del Nivel 0).
Cada notebook va en `notebooks/L01_cargar_csv_tsv.ipynb`, etc.

REQUISITOS ESTRUCTURALES (idénticos en todas las lecciones):

1. PRIMERA CELDA (markdown): título de la lección, y una tabla con
   "Qué vas a aprender" / "Cuánto tiempo" / "Qué datasets usa".
2. Segunda celda (code): celda de setup. Debe ser SIEMPRE la misma, y así:
   - `import pandas as pd, numpy as np, matplotlib.pyplot as plt`
   - `%matplotlib inline`
   - una llamada a `plt.style.use("seaborn-v0_8-whitegrid")`
   - carga de los datos de la lección con los parámetros CORRECTOS para cada fichero
     (ojo: uno es `sep=";" decimal="," encoding="latin-1"`, otro es `sep="\t"`, otro
     tiene BOM `encoding="utf-8-sig"`). Pon un comentario explicando POR QUÉ cada
     parámetro es ese, porque esa es la lección en sí.
   - un print de `df.shape` y `df.dtypes`.
3. Celdas de contenido, en este orden y con estos títulos markdown exactos:
   - `## El concepto`
   - `## Manos a la obra`
   - `## ⚠️ La trampa`
   - `## 🧪 Tu turno`  (2-4 ejercicios con celdas de código vacío debajo, con `# TU CÓDIGO AQUÍ`)
   - `## 📦 Workbook integrador`  (el caso real de la lección, según PLAN.md)
4. El workbook integrador debe terminar con una celda que **escriba un fichero de
   verdad** (`diagnostico_carga.csv`, `ficha_ventas.csv`, `reporte_mensual.xlsx`, etc.)
   y un print de confirmación con la ruta. Nada de ejercicios que se queden en la
   memoria: cada lección tiene que producir un artefacto en disco.
5. En el workbook integrador, incluye siempre una celda markdown con
   "### Criterios de aceptación", listando 3-5 condiciones concretas y verificables
   (nº de filas exactas, columnas obligatorias, formato del fichero de salida).

REQUISITOS DE ESTILO:
- Todo el texto en español de España, con tildes correctas. Los nombres de variables,
  funciones y ficheros en inglés (es lo estándar en data).
- Comentarios en código que expliquen el POR QUÉ, no el QUÉ. Nada de `# suma las columnas`.
- Usa el API moderno de pandas: `df.query("ventas > @media")` en vez de máscaras equivalentes
  cuando se pueda, `df.loc[]`, `.assign()` en vez de mutar. No uses nada que esté
  deprecado en pandas 2.x/3.x (`df.append`, `inplace=True` en cadenas, `resample("M")`
  — usa "ME").
- Empieza cada notebook con un admonition de "qué vas a poder hacer al terminar".
- Los gráficos que aparezcan: con `fig, ax = plt.subplots()` (API OO, nunca `plt.*`
  suelto después), con `plt.tight_layout()`, título con la unidad, y `ax.grid(axis="y")`.
  Nada de gráficos 3D, nada de sombras, y máximo 3 colores.
- Convierte las salidas a texto antes de hacerlas grandes (>12 filas) para que no
  reviente el notebook.

VALIDACIÓN (obligatoria, no opcional):
- Ejecuta cada notebook con `jupyter nbconvert --to notebook --execute --inplace` o con
  `nbformat` + `nbclient`.
- Si una celda falla, ARREGLA el código del notebook y vuelve a ejecutar. No me
  entregues un notebook con errores.
- Al terminar, dime qué ficheros ha escrito cada notebook y con cuántas filas.

AHORA: lee PLAN.md, genera las lecciones 1 a 6, ejecútalas todas y dime qué ha pasado.
```

Para otras lecciones, cambia:
- "lecciones 1 a 6" → "lecciones 7 a 13", "14 a 20", etc.
- Los requisitos estructurales son los mismos, pero en el Nivel 3 (lecciones 21-26)
  cambia el punto 6 por: "prioriza la calidad visual de los gráficos; usa seaborn cuando
  simplifique, y aplica un tema consistente."

---
---

# PROMPT 3 — Revisión y control de calidad de lo generado

```
Acabas de generar los notebooks de las lecciones X a Y en `notebooks/`. Ahora haz una
revisión crítica de tu propio trabajo. NO me digas que todo está bien sin comprobarlo.

Revisa punto por punto:

1. EJECUCIÓN. Ejecuta cada notebook de verdad. Lista cualquier celda que falle, con el
   traceback exacto. Arregla y re-ejecuta hasta que todos pasen.

2. DATOS REALES vs DATOS INVENTADOS. Cada dataset del `generar_datasets_sucios.py`
   tiene un "Expected Answer" impreso al final del script (delimitador, encoding,
   nº de filas, anomalías principales). Contrasta lo que dicen los notebooks contra
   esas cifras. Si un notebook afirma "el CSV tiene 8 columnas" y el fichero tiene 9,
   es un bug. Repara la afirmación.

3. AFIRMACIONES TÉCNICAS. Busca afirmaciones en los notebooks que sean técnicamente
   incorrectas o dudosas, especialmente:
   - sobre qué hace `casefold` vs `lower` vs `upper` con İ, ı, ß, ẞ
   - sobre `resample("M")` vs `"ME"` en pandas 2.2+/3.x
   - sobre `merge` y multiplicación de filas
   - sobre dtype `str` en pandas 3
   Verifícalas ejecutando Python de verdad, no de memoria. Si alguna es falsa,
   corrígela y escribe la versión correcta con su explicación.

4. CALIDAD DIDÁCTICA. ¿El workbook integrador se parece a un problema real de empresa,
   o a un ejercicio artificial? ¿Produce un artefacto en disco? ¿Tiene
   criterios de aceptación verificables? ¿Un principiante podría resolverlo con lo
   aprendido hasta esa lección, ni más ni menos?

5. CONSISTENCIA entre notebooks: mismos nombres de variables, mismos colores, mismo
   estilo de comentarios, misma estructura de títulos.

6. CÓDIGO MUERTO: imports sin usar, variables definidas y nunca usadas, celdas de
  setup duplicadas, output de celdas que ya no corresponde al código.

Al final dame un informe con: (a) lista de bugs encontrados y arreglados, (b) lista de
mejoras de calidad aplicadas, (c) cualquier afirmación técnica que tuvieras mal y cómo
la corregiste. Sé concreto y cita archivos y celdas.
```

---
---

# PROMPT 4 — La lección de alfabetos (caso especial, usa cuando llegues a la L10)

```
Genera `notebooks/L10_alfabetos_no_latinos.ipynb`. Esta lección tiene requirements
especiales porque es la que más gente hace mal, y ya tengo los datosQBake generados en
`datos/clientes_crm.csv` (encoding utf-8-sig).

El notebook tiene que DEMOSTRAR las trampas con código, no contarlas. Estructura:

1. `## El concepto` — qué es Unicode y por qué "el mismo nombre" puede ser 3 cadenas
   distintas.

2. `## Demostración 1: el turco I/ı/İ` — una celda de código que imprima, para los
   caracteres `I`, `İ`, `ı`, `i`:
   - su `unicodedata.name()` y su code point en hexadecimal
   - `len()`, `len(lower())`, `len(casefold())`
   - si `lower()` y `casefold()` dan el mismo resultado
   Luego muestra explícitamente que `"Ibrahim" == "ıbrahim"` es `False`, y explica que
   es CORRECTO según Unicode pero que rompe un join de dos sistemas, uno de ellos turco.

3. `## Demostración 2: casefold alarga la cadena` — `ß` → `ss`, `ẞ` → `ss`. Muestra la
   tabla de longitudes. Explica por qué esto rompe cualquier código que asuma
   "1 carácter = 1 letra".

4. `## Demostración 3: caracteres que se parecen y NO son iguales` — una tabla con
   `ş` (U+015F, turco, cedilla), `ș` (U+0219, rumano, below), `ś` (U+015B, polaco),
   `s` (U+0073). Enséñalos en mayúscula y minúscula. Comprueba con `==` que son
   distintos. Esto se ve fatal en un catálogo de productos.

5. `## Demostración 4: el árabe` — muestra que:
   - el tashkil suma caracteres invisibles: `len("أحمد") != len("أَحْمَد")` aunque se
     vean iguales
   - hay marcas de dirección RTL (U+200F) y de LTR (U+200E)
   - `unidecode("محمد")` da `"mhmd"`, una aproximación que pierde información
   - Por eso NUNCA debes validar texto árabe con `len()` ni unirlo por transliteración
     sin marcar el riesgo.

6. `## Demostración 5: los europeos` — `ł→l`, `ø→o`, `đ→d`, `æ→ae`, `þ→th`, `ð→d`.
   Tabla original → `unidecode` → y una columna de "puede colisionar con" (ej. `ł` y `l`
   se vuelven ambos `l`).

7. `## La solución: una clave canónica en capas` — implementa y explica:
   ```python
   def clave_canonica(s):
       s = unicodedata.normalize("NFKD", s)
       s = "".join(c for c in s if not unicodedata.combining(c))
       s = s.casefold()
       s = unidecode(s)
       s = re.sub(r"[^a-z0-9]+", " ", s)
       return re.sub(r"\s+", " ", s).strip()
   ```
   Explica línea a línea por qué el orden importa (si haces `unidecode` ANTES de quitar
   los diacríticos, `ü` se convierte en `u` y pierdes la información de que era acentuada).

8. `## ⚠️ La trampa` —celda dedicada: tu función de clave canónica va a FUSIONAR personas
   distintas (`Łukasz` y `Lukasz` → `lukasz`). Muestra cuántos casos de eso hay en el
   dataset real. Un join al 100% de fusión no es gratis.

9. `## 🧪 Tu turno` — 4 ejercicios: contar cuántos nombres tienen caracteres no latinos;
   encontrar los nombres que se hacen igual bajo la clave canónica pero son distintos
   en el original; detectar cuántos clientes tienen tashkil; y un ejercicio de para
   qué sirve y para qué NO sirve `unidecode`.

10. `## 📦 Workbook integrador: normalización multilingüe` — con `datos/clientes_crm.csv`:
    - aplica la clave canónica
    - cuenta cuántos clientes se colapsan
    - **estima la tasa de falsos positivos** cruzando país y email
    - exporta `fusiones_sospechosas.csv` con los grupos que un humano debería revisar
    - criteria de aceptación con números concretos

Criterios de estilo: todo en español, comentarios explicando el porqué, celdas de salida
cortas, y un `print` con las cadenas comparadas usando `repr()` para que se vean los
caracteres invisibles (`repr("أَحْمَد")` muestra los combining marks).

Ejecuta el notebook y verifica que todas las celdas corren. Dime cuántas fusiones
encuentra y cuál es la tasa de falsos positivos estimada.
```

---
---

# PROMPT 5 — Visualización: de "funciona" a " professionalism"

```
Genera `notebooks/L21_visualizacion_profesional.ipynb` y su hermano
`notebooks/L24_rediseno_de_graficos.ipynb`. Esta es la parte de visualización del curso,
así que el listón es: lo que se vea tiene que parecer hecho por alguien que sabe, no por
un tutorial de 2015.

REQUISITOS COMUNES:
- `plt.style.use("seaborn-v0_8-whitegrid")` como base, y sobre eso define un tema propio
  con `plt.rcParams.update({...})` en una celda de setup.
- Define una paleta de 3-4 colores con significado fijo en todo el curso, por ejemplo:
  azul = categoría A, naranja = categoría B, gris = referencia, rojo = alerta. Deja ese
  diccionario en una celda y ÚSALO en todos los gráficos.
- Todos los gráficos: `fig, ax = plt.subplots(...)`, `fig.tight_layout()`, título con la
  UNIDAD (`"Ventas mensuales (miles de €)"`), y `ax.grid(axis="y", alpha=0.3)`.

PROHIBIDO (y revísate al final para asegurarte):
- gráficos 3D
- sombras, bordes decorativos, texturas
- más de 5 colores en un gráfico
- leyenda cuando puedes etiquetar las barras directamente
- ejes Y que no empiezan en cero en gráficos de barras
- `plt.` suelto cuando ya tienes un `ax`

L21 — contenido:
1. Por qué el API dual de matplotlib (`plt.*` vs `ax.*`) te va a morder, con ejemplo.
2. Anatomía de un gráfico decente: qué quitar primero (caja, rejilla pesada, ticks de más,
   3D, sombra), y en qué orden.
3. Elegir el gráfico correcto según la PREGUNTA: comparación (barra), evolución (línea),
   distribución (histograma/box), relación (scatter), composición (apilado, con cuidado).
   Da un ejemplo de cada uno con el dataset de ventas.
4. Ordenar por valor (no alfabético) en un gráfico de barras; y por qué la barra
   horizontal es mejor que la vertical para nombres largos.
5. Anotar directamente en vez de usar leyenda.
6. Subplots: cuándo 1x1, cuándo 2x2, cuándo facets de seaborn.
7. Exportar: `savefig` a PNG (dpi=200), SVG (vectorial, para imprimir) y PDF. Explica
   cuándo usar cada uno. Remember: `savefig` ANTES de `show()` en un script, y en un
   notebook da igual, pero con `bbox_inches="tight"` para que no corte las etiquetas.

L24 — contenido (este es el más divertido y el más útil):
1. Pon 3 gráficos mal hechos A PROPÓSITO usando los datos reales: uno con 13
   colores y 20 en la leyenda, uno en 3D, uno con el eje Y truncado en 80 (que exagera
   una diferencia del 2%).
2. Explica por qué mienten: el de barras truncadas hace
   que un +2% parezca un +40%.
3. Rehaz los tres bien aplicando las reglas.
4. Pon los 6 gráficos juntos (antes/después) en una figura 3x2 para comparar.
5. Ejercicio: dale al alumno 3 gráficos nuevos "mal hechos" y que los arregle.

Cierra los dos notebooks con un `## 📦 Workbook integrador` que genere un mini-dashboard
de 6 gráficos con el tema consistente y lo exporte a las 3 formatos (PNG, SVG, PDF) más
un HTML con `fig.write_html` de una versión plotly. Con criterios de aceptación.

Ejecuta ambos notebooks y comprueba que los ficheros exportados existen.
```

---
---

# PROMPT 6 — El proyecto final (úsalo al terminar el nivel 4)

```
Genera el proyecto capstone: un pipeline completo de datos de retail.

Situación: una empresa tiene 4 ficheros sucios en `datos/` que exportan 4 sistemas
distintos (ERP español, ERP inglés, CRM,extracto bancario). El CFO pide cada mes un
informe de ventas por región y categoría, con margen, ticket medio, y una recomendación
sobre dónde invertir el presupuesto de marketing.

Quiero que construyas, en este orden:

1. `src/limpiar_ventas.py` — un módulo de funciones puras, sin efectossecondary, que
   cargue y limpie cada fuente. Reglas obligatorias:
   - una función por preocupación (`cargar_erp`, `normalizar_texto`, `parsear_importes`,
     `validar`, ...)
   - `validate=` en cada merge
   - `errors="coerce"` + recuento de losses en cada conversión de tipo
   - NINGÚN `inplace=True`
   - docstring en cada función que diga qué hace y qué devuelve
   - que sea importable: `python -c "from src.limpiar_ventas import pipeline; pipeline()"`

2. `tests/test_limpiar_ventas.py` — mínimo 10 tests con pytest: nulos, tipos, rangos,
   unicidad de clave, e **invariantes de negocio** (ej. "el total facturado del pipeline
   limpio debe estar entre el 95% y el 105% del total crudo", porque los descartes
   justificados no pueden eliminar más de un 5% de la facturación). Ejecuta `pytest -v` y
   pásalos todos.

3. `notebooks/capstone_informe.ipynb` — el informe:
   - carga con el pipeline
   - 4-5 visualizaciones con el tema del curso
   - una sección de CALIDAD DE DATOS con las métricas antes/después
   - el informe en PDF con `jupyter nbconvert --to pdf`

4. `docs/recomendacion.md` — UNA PÁGINA. Qué dice el dato, qué recomienda hacer, y qué
  Supuestos tiene. Sin gráficos decorativos, con los números que sostienen la
   recomendación citados textualmente.

Regla de oro: el código va en `.py` y es testeable; el notebook solo llama al módulo y
visualiza. Nada de lógica de negocio dentro del notebook.

Ejecuta pytest, ejecuta el notebook, genera el PDF, y dame el resumen: filas de entrada
vs salida, % de datos descartados por categoría, y los 3 números que sostienen tu
recomendación.
```

---
---

# Cómo encajar esto con tu flujo real

```bash
# 1. Preparar entorno (una vez)
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy matplotlib seaborn plotly openpyxl unidecode regex \
            nbformat nbconvert ipykernel pytest papermill kaleido

# 2. Instalar el kernel de Jupyter para este venv
python -m ipykernel install --user --name pandas-es --display-name "Python (pandas-es)"

# 3. Generar los datos
python generar_datasets_sucios.py

# 4. Lanzar JupyterLab apuntando al kernel del venv
jupyter lab --notebook-dir=. \
            --ServerApp.default_kernel_name=pandas-es \
            --ServerApp.token='' --no-browser
```

Si prefieres un kernel siempre activo, añade esto a tu `~/.ipython/profile_default/startup/00-pandas.py`
para que `pd` ya venga con el estilo aplicado al abrir cualquier notebook:

```python
import pandas as pd
pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 200)
pd.set_option("display.float_format", lambda v: f"{v:,.2f}")
```
