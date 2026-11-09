"""
Fase 36B: genera, desde los resultados guardados, el informe técnico, el registro de procedencia, el resumen de pruebas y el informe de integridad.

Uso, desde analisis/: python fase36/scripts/generar_informes.py
Solo lee resultados ya construidos. Escribe en fase36/informes/. La línea --manifiesto escribe además integridad/manifiesto_final_36B.csv.
"""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(AQUI), str(AQUI.parent / 'revision_correctiva_fase34')]
sys.dont_write_bytecode = True

import configuracion_fase36 as C  # noqa: E402
from manifiesto import huella  # noqa: E402

INF = AQUI / 'informes'


def c(x, d=4):
    return f'{float(x):.{d}f}'.replace('.', ',').replace('-', '−')


def valor_validacion(x):
    """Diferencias diminutas en notación científica; recuentos e inercias en decimal, con coma."""
    v = float(x)
    if v == 0:
        return '0'
    if abs(v) < 1e-3:
        return f'{v:.1e}'
    return f'{v:.4f}'.rstrip('0').rstrip('.').replace('.', ',')


def tabla_md(cab, filas):
    return '\n'.join(['| ' + ' | '.join(cab) + ' |', '|' + '---|' * len(cab)] + ['| ' + ' | '.join(str(x) for x in f) + ' |' for f in filas])


def leer(ruta, **k):
    return pd.read_csv(ruta, encoding='utf-8', **k)


def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto.strip() + '\n', encoding='utf-8', newline='\n')


def informe_tecnico():
    res = json.loads((AQUI / 'matrices' / 'resumen_matrices.json').read_text(encoding='utf-8'))
    par = leer(AQUI / 'artefactos' / 'parametros_escalado.csv')
    gru = leer(AQUI / 'artefactos' / 'agrupaciones_categorias.csv', dtype={'grupo': str, 'niveles': str})
    val = leer(AQUI / 'validacion' / 'validacion_famd.csv', dtype=str)
    meta = json.loads((AQUI / 'validacion' / 'validacion_famd.json').read_text(encoding='utf-8'))
    pes = json.loads((AQUI / 'sensibilidades' / 'pesos_bloques.json').read_text(encoding='utf-8'))['escenarios']
    cat = leer(AQUI / 'sensibilidades' / 'catalogo_sensibilidades.csv')
    desc = {'P1': 'PCA con IMC', 'P2': 'PCA sin IMC', 'F1': 'FAMD con IMC', 'F2': 'FAMD sin IMC'}
    t_dim = tabla_md(['Matriz', 'Ruta', 'Filas', 'Columnas', 'Varianza o inercia total'],
                     [[f'`{C.NOMBRE_ARCHIVO[e]}.csv`', desc[e], res[e]['filas'], res[e]['columnas'], c(res[e]['inercia'])] for e in C.ESCENARIOS])
    p1 = par[par['escenario'] == 'P1']
    z = p1[p1['clase'] == 'z']
    t_z = tabla_md(['Columna', 'Media', 'DE', 'n de referencia'], [[f'`{f.columna}`', c(f.media), c(f.de), f.n_referencia] for f in z.itertuples()])
    no = p1[p1['clase'] != 'z']
    t_nom = tabla_md(['Columna', 'p', 'Divisor'], [[f'`{f.columna}`', c(f.p), c(f.divisor)] for f in no.itertuples()])
    t_gru = tabla_md(['Variable', 'Grupo', 'n', 'p', 'Máximo de la columna'], [[f'`{f.variable}`', f.grupo, f.n_529, c(f.p), c(f.valor_maximo_columna, 2)] for f in gru.itertuples()])
    t_val = tabla_md(['Sección', 'Comprobación', 'Obtenido', 'Resultado'],
                     [[f.seccion, f.comprobacion, valor_validacion(f.obtenido), f.resultado] for f in val.itertuples()])
    bloques = list(pes['F1']['multiplicador_por_bloque'])
    t_blo = tabla_md(['Bloque', 'Inercia P1', 'Multiplicador P1', 'Inercia F1', 'Multiplicador F1'],
                     [[b, c(pes['P1']['inercia_por_bloque'][b], 3), c(pes['P1']['multiplicador_por_bloque'][b], 3), c(pes['F1']['inercia_por_bloque'][b], 3), c(pes['F1']['multiplicador_por_bloque'][b], 3)] for b in bloques])
    t_sen = tabla_md(['Sensibilidad', 'Base', 'Columnas', 'Ajuste', 'Proyección', 'Inercia en 529'],
                     [[f.sensibilidad, f.base, f.columnas, f.filas_ajuste, f.filas_proyeccion, c(f.inercia_en_529)] for f in cat.itertuples()])
    ref = meta['referencia_externa']
    escribir(INF / 'fuentes' / '04_informe_tecnico_codificacion_escalado.md', f"""
# 1. Resumen

Se prepararon cuatro matrices de 529 filas para PCA y FAMD, sin ajustar ningún modelo. Las cifras salen de los archivos guardados en `analisis/fase36/`.

{t_dim}

Todas las columnas tienen media cero en las 529. **La validación matemática de FAMD fue {meta['veredicto'].lower()}: {meta['cumplen']} de {meta['comprobaciones']} comprobaciones cumplen**, por lo que F1 y F2 pueden llamarse FAMD, con la precisión de la sección 6 sobre el IMC.

# 2. Entradas

- **Valores:** `datos/limpio_usuaria/dataset_usuaria_limpio.csv`, con las 529 de `datos/analitico/dataset_fase35.csv`, en el orden de este último.
- **Niveles y roles:** `fase36_diseno/diccionario_codificacion_fase36.csv` y `matriz_decisiones_variables.csv`.
- **Procedencia:** reconstrucción en memoria desde `datos/sintetico/dataset_usuaria_sucio.csv`.
- **Identificador:** solo `participante_id`, un número sin datos personales, en `matrices/identificadores.csv`. Las matrices no lo incluyen: la fila N corresponde a la fila N de ese archivo.

# 3. Codificación

| Tipo | Regla | Ejemplo |
|---|---|---|
| Binaria | Código 0/1 | `tiene_pareja`: NO = 0, SI = 1 |
| Ordinal | Código consecutivo del instrumento | `frutas_dia`: 1 a 5 |
| Frecuencia de ejercicio | 0 y 1 → 0; 2 → 1; 3 → 2; 4 → 3; 5 → 4 | «No lo realiza» y «Nunca» = 0 |
| Cantidad de personas | Vacío con `cuida_otras_personas` = NO → 0; 1, 2, 3 | «No cuida» = 0 |
| Nominal | Indicadoras | `quien_prepara_comidas` |

El diccionario completo está en `artefactos/diccionario_codificacion_36B.csv`. **Supuesto explícito:** los códigos consecutivos suponen pasos iguales entre niveles; S-ORD lo contrasta con ridit, calculado sobre la escala del instrumento.

# 4. Por qué StandardScaler

RobustScaler no falla cuando el rango intercuartílico es cero: scikit-learn sustituye esa escala por 1. No se usa por adecuación al diseño. Aplicado a las 28 columnas numéricas con referencia en las 529, nueve conservarían su unidad original, y la varianza iría de 0,14 a 2,26. Con StandardScaler todas valen 1, y las cuantitativas quedan como FAMD las define.

# 5. Parámetros de escalado

Se calculan con `ddof = 0`. Son iguales en las rutas PCA y FAMD para las columnas que comparten.

{t_z}

**Indicadoras de la ruta PCA.** Valor: `(I − p) / divisor`.

{t_nom}

Todas las proporciones de FAMD están en `artefactos/parametros_escalado.csv`.

# 6. IMC

- **Parámetros:** media 29,2296 y DE 6,2636, de las 267 observadas.
- **Imputadas:** las 262 quedan en z = 0 exacto.
- **Varianza en las 529:** 267/529 = 0,5047, igual en P1 y F1. Entre las 267 observadas, la DE es 1.
- **Sin doble estandarización:** el transformador no reescala después y la columna es idéntica en ambas rutas.

**Precisión.** F1 no es una FAMD estándar en esa columna: el método original daría varianza 1 a cada cuantitativa. F1 aplica un peso reducido deliberado, y por eso `prince`, que reestandariza, no puede reproducir F1. Se comparó en el caso estándar, y el peso reducido se validó con el criterio ponderado (sección 8). F2, sin IMC, es FAMD estándar.

# 7. Agrupaciones de categorías en FAMD

{t_gru}

Los grupos están fijados de antemano y todos superan el 5 %. En las sensibilidades de proyección se mantienen iguales; el grupo menor sigue en 5,5 % a 5,7 %.

# 8. Validación matemática de FAMD

Se usaron datos sintéticos (n = 400, semilla 42) con cuatro cuantitativas y tres categóricas de 2, 3 y 4 niveles. **No se ajustó FAMD sobre los datos del estudio.**

La referencia externa fue `prince` {ref.get('version', '')}, instalada en una carpeta temporal fuera del proyecto: las dependencias no cambiaron. `prince` y la transformación propia dieron los mismos valores propios y coordenadas, con diferencias del orden de 1e-14.

{t_val}

**Qué demuestra:**

- la ponderación de categorías y la inercia total son las de FAMD;
- la transformación coincide con cuatro derivaciones independientes y con una implementación externa;
- si la ponderación fuera incorrecta, el criterio de Pagès lo detectaría (control negativo).

**Qué no demuestra:** que los ejes del estudio sean interpretables, ni que exista estructura de clústeres. Eso corresponde a la Fase 37.

**Hallazgo.** `prince` recalcula las proporciones con los datos que recibe al proyectar: con una sola fila, el resultado cambia. La transformación propia las mantiene congeladas. Por eso `prince` no debe usarse para proyectar participantes en la Fase 40.

# 9. Valores desconocidos y participantes nuevas

| Caso | Regla |
|---|---|
| Nivel no admitido | Error, sin perfil |
| Nivel válido no observado | Se transforma normalmente, con marca si queda fuera del rango |
| Pregunta condicional no mostrada | Nivel estructural de cero, con marca |
| Pregunta madre ausente | Nivel estructural, igual que la limpieza, con marca |
| IMC ausente | z = 0, con marca |
| Otra respuesta ausente | Valor congelado, con marca y aviso. Límite pendiente (D-09) |

Los valores congelados están en `valores_desconocidos.json`. Salen solo de respuestas no imputadas: moda en binarias y nominal, mediana inferior en ordinales, y mediana en `edad` y `horas_sedentarismo`. En las preguntas condicionales se calculan entre quienes sí responden.

# 10. Artefactos

```text
analisis/fase36/
  matrices/        4 matrices, identificadores y resumen
  artefactos/      P1, P2, F1, F2: esquema, orden, codificadores, escaladores, desconocidos,
                   procedencia, entorno y huellas; además diccionario, parámetros, agrupaciones
                   y esquema para nuevas participantes
  procedencia/     celdas, resumen y contraste con auditorías
  modulos/         laboral y cuidados, sin escalar
  sensibilidades/  poblaciones, catálogo, pesos de bloques y 20 matrices preparadas
  validacion/      FAMD con datos de prueba
  pruebas/         resultados y control de mutaciones
  integridad/      archivos leídos, escrituras y manifiestos
```

Los parámetros se guardan en JSON, sin pickle, y `transformador.py` solo depende de NumPy y pandas.

# 11. Sensibilidad de ponderación por bloques

Preparada, sin aplicar a clústeres. Cada bloque recibiría la misma inercia, y la inercia global se conserva.

{t_blo}

**Advertencia.** El bloque de medidas solo contiene el IMC, de modo que S-BLOQUE lo amplificaría por 2,70 o 3,09, aunque la mitad de esa columna es un valor imputado.

# 12. Catálogo de sensibilidades preparadas

Ninguna se ejecutó. Las filas de proyección quedan con media distinta de cero por diseño, y por eso la inercia en las 529 difiere de la de referencia.

{t_sen}

""")


def registro_procedencia():
    res = leer(AQUI / 'procedencia' / 'resumen_por_variable.csv')
    con = leer(AQUI / 'procedencia' / 'contraste_auditorias.csv')
    t = tabla_md(['Variable', 'Observada', 'Deducida', 'Imputada', 'No aplicable', 'Faltante', 'Vacías por previa imputada'],
                 [[f'`{f.variable}`', f.observada, f.deducida, f.imputada, f.no_aplicable, f.faltante, f.heredadas] for f in res.itertuples()])
    fuentes = con.groupby('fuente')['coincide'].agg(['size', 'sum']).reset_index()
    tc = tabla_md(['Auditoría histórica', 'Recuentos comparados', 'Coinciden'], [[x[0], x[1], x[2]] for x in fuentes.to_numpy()])
    g = res[res['variable'].isin(C.GENERALES)]
    n_imp = int(g['imputada'].sum())
    escribir(INF / '05_registro_procedencia_imputaciones.md', f"""
# Fase 36B: registro de procedencia e imputaciones

**Detalle por celda:** `procedencia/procedencia_celdas.csv`, con 17.457 filas (529 × 33): identificador, variable, valor original, estado y marca de pregunta previa imputada. **Ninguna de estas marcas entra a las matrices.**

## Método

La limpieza 34B se repite en memoria sobre el conjunto sucio y se exige que coincida con el archivo limpio en todas las celdas. Una celda es:

| Estado | Criterio |
|---|---|
| Imputada | Vacía justo antes del paso 9 y con valor en el limpio; en el IMC, vacía en el limpio y con la media de la Fase 35A |
| Deducida | Vacía antes del paso 8 y con valor antes del paso 9 |
| Observada | El resto de las celdas con valor |
| No aplicable | Vacía porque la pregunta no se mostró |
| Faltante | Vacía aunque la pregunta aplicaba: las respuestas laborales de las 22 con trabajo imputado |

No se leyó la verdad del simulador ni la bitácora. Lo confirma un gancho de auditoría de Python: `integridad/archivos_leidos.csv`. Este módulo tampoco importa `auditoria_fase34`, que sí las carga.

## Contraste con las auditorías

{tc}

Además, en las 16 variables con marca `_imputado` en el limpio, la máscara coincide **celda a celda**, no solo en el recuento.

## Recuento por variable (529 participantes)

{t}

## Totales de las 30 variables generales

- **Imputadas: {n_imp} de 15.870 ({100 * n_imp / 15870:.1f} %).** Son 665 de la limpieza 34B y 262 de IMC en la Fase 35A. El diseño citaba solo las 665.
- **Valores estructurales que dependen de una pregunta previa imputada:** {int(g['heredadas'].sum())} (21 de cuidado, y 29, 22 y 28 de ejercicio).

## Poblaciones afectadas

| Grupo | n | Pregunta imputada | Tratamiento |
|---|---|---|---|
| Trabajo imputado como Sí | 22 | `trabaja_actualmente` | Siguen en la capa general; fuera del módulo laboral, porque no tienen respuestas. S-TRA |
| Cuidado imputado como No | 21 | `cuida_otras_personas` | Su cantidad = 0 no es respuesta observada. S-CUI |
| Ceros de ejercicio heredados | 75 (unión de 29, 22 y 28) | `realiza_*` | Su frecuencia = 0 no es respuesta observada. S-EJE |

Listas: `sensibilidades/poblaciones/`.

## Valores que no entran a los módulos

Los 220 valores 0 de quienes no trabajan y los 22 valores 3 de relleno de `dataset_fase35.csv` no aparecen: los módulos se toman del conjunto limpio.
""")


def resumen_pruebas():
    t = leer(AQUI / 'pruebas' / 'resultados_pruebas.csv')
    m = leer(AQUI / 'pruebas' / 'control_mutaciones.csv')
    filas = [[f.numero, f.grupo, f.prueba, f.resultado, f.detalle] for f in t.itertuples()]
    mf = [[f.error_introducido, f.prueba, 'Sí' if f.detectado else 'No'] for f in m.itertuples()]
    ok = int((t['resultado'] == 'OK').sum())
    escribir(INF / '06_resultados_pruebas.md', f"""
# Fase 36B: resultados de las pruebas

**{ok} de {len(t)} pruebas superadas.** 25 vienen de `plan_pruebas_fase36.md` y 7 se agregaron en este encargo. Ninguna quedó con fallo sin resolver. Se repiten con `python fase36/pruebas_fase36.py`.

{tabla_md(['N.º', 'Grupo', 'Prueba', 'Resultado', 'Detalle'], filas)}

## Control de mutaciones

Las 32 pruebas pasaron en la primera ejecución completa, de modo que se comprobó que pueden fallar. Se introdujeron errores en memoria, sin tocar los archivos, y cada prueba correspondiente debía detectarlos: **{int(m['detectado'].sum())} de {len(m)} detectados**.

{tabla_md(['Error introducido', 'Función de prueba', 'Detectado'], mf)}

## Alcance

- No se evaluó la calidad de clústeres ni la varianza explicada, porque corresponden a la Fase 37.
- La equivalencia de FAMD se probó con datos sintéticos, no con las matrices reales.
- La comparación con `prince` necesita indicar su carpeta con `--referencia`. Sin esa opción, la prueba 26 ejecuta las demás comprobaciones.
""")


def informe_integridad():
    def git(*a):
        return subprocess.run(['git', *a], cwd=C.RAIZ, capture_output=True, text=True, encoding='utf-8').stdout.rstrip()
    base = pd.read_csv(C.MANIFIESTO_CIERRE, encoding='utf-8').set_index('ruta')['sha256']
    distintos = [r for r, h in base.items() if not (C.RAIZ / r).exists() or huella(C.RAIZ / r) != h]
    por_carpeta = pd.Series([r.split('/')[0] + '/' + r.split('/')[1] if r.count('/') > 1 else r.split('/')[0] for r in base.index]).value_counts()
    leidos = leer(AQUI / 'integridad' / 'archivos_leidos.csv')['archivo_leido'].tolist()
    estado = git('status', '--short').splitlines()
    tracked = sorted(x[3:] for x in estado if not x.startswith('??'))
    nuevos = [x[3:] for x in estado if x.startswith('??') and 'fase36' in x]
    escribir(INF / '07_informe_integridad.md', f"""
# Fase 36B: informe de integridad

## Resultado

**{len(base) - len(distintos)} de {len(base)} archivos coinciden** con `cierre_fases_34_35/integridad/manifiesto_despues.csv`, por SHA-256. {'Ningún archivo histórico cambió.' if not distintos else 'Distintos: ' + ', '.join(distintos[:10])}

| Comprobación | Resultado |
|---|---|
| Commit | {git('rev-parse', '--short', 'HEAD')} (sin cambios) |
| Archivos preparados para commit | {len(git('diff', '--cached', '--name-only').splitlines())} |
| Datasets históricos | Sin cambios (`datos/`, {int(sum(1 for r in base.index if r.startswith('datos/')))} archivos) |
| Shannon, FCBF y Random Forest | Sin cambios y sin ejecutar |
| Plataforma AgingWomen (`src/`) | Sin cambios |
| Diseño 36A (`fase36_diseno/`) | Sin modificar |
| Commit o push | No se hizo |
| Dependencias del proyecto | Sin cambios; `prince` solo en una carpeta temporal |

## Manifiesto de partida, por carpeta

{tabla_md(['Carpeta', 'Archivos'], [[f'`{k}`', int(v)] for k, v in por_carpeta.head(14).items()])}

## Archivos leídos por la construcción

Registrados con un gancho de auditoría de Python, no declarados a mano. La verdad del simulador y la bitácora no aparecen, y no hubo escrituras fuera de `analisis/fase36/`.

{chr(10).join('- `' + x + '`' for x in leidos)}

## Estado de git

**Archivos modificados con seguimiento ({len(tracked)}).** Son los mismos 8 de la corrección controlada del cierre; la Fase 36B no agregó ninguno:

{chr(10).join('- `' + x + '`' for x in tracked)}

**Nuevo en esta fase:** {', '.join('`' + x + '`' for x in nuevos if x.rstrip('/').endswith('fase36'))}. El resto de archivos sin seguimiento ya existía.

## Manifiesto de esta fase

- `integridad/manifiesto_fase36.csv`: lo que produce la construcción. Es determinista: dos procesos distintos dan los mismos SHA-256.
- `integridad/manifiesto_final_36B.csv`: toda la carpeta `analisis/fase36/`, incluidos código e informes.

## Nota sobre el verificador del diseño

`fase36_diseno/scripts/verificar_diseno.py` marcará ahora «existe carpeta de implementación». Es esperado, porque su comprobación solo valía antes de la Fase 36B. No se volvió a ejecutar, para no reescribir su registro.
""")


def manifiesto_final():
    salida = AQUI / 'integridad' / 'manifiesto_final_36B.csv'
    archivos = sorted(p for p in AQUI.rglob('*') if p.is_file() and p != salida and '__pycache__' not in p.parts)
    with salida.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['ruta', 'sha256', 'bytes'])
        for p in archivos:
            w.writerow([p.relative_to(AQUI).as_posix(), huella(p), p.stat().st_size])
    print('Manifiesto final:', len(archivos), 'archivos;', round(sum(p.stat().st_size for p in archivos) / 1e6, 1), 'MB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifiesto', action='store_true')
    if ap.parse_args().manifiesto:
        manifiesto_final()
        return
    informe_tecnico()
    registro_procedencia()
    resumen_pruebas()
    informe_integridad()


if __name__ == '__main__':
    main()
