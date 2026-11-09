"""
Corrección controlada de la Fase 34: versiones revisadas de los informes 34B, 34C, 34D y 34E.

Uso, desde la raíz del proyecto:
    python analisis/revision_correctiva_fase34/generar_informes_revisados.py

Copia cada informe histórico, aplica correcciones de texto y notas, y lo guarda en informes_revisados/.
Cada corrección exige que su texto de anclaje exista exactamente una vez; si no, se detiene sin guardar.
Las cifras nuevas salen de tablas/; ningún análisis se ejecuta. Los históricos solo se leen.
Escribe también tablas/relacion_correcciones.csv: qué cambió, dónde y por qué hallazgo.
"""
import re
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
ANALISIS = AQUI.parent
RAIZ = ANALISIS.parent
TABLAS = AQUI / 'tablas'
SALIDA = AQUI / 'informes_revisados'
FIG_REVISADAS = AQUI / 'figuras_34D_revisadas'
BITACORA = []


def leer(nombre):
    return pd.read_csv(TABLAS / f'{nombre}.csv', encoding='utf-8-sig')


def n1(x):
    return f'{x:.1f}'.replace('.', ',')


def n3(x):
    return f'{x:.3f}'.replace('.', ',')


def pv(x):
    return '< 0,001' if x < 0.001 else n3(x)


def tabla(encabezado, filas):
    lineas = ['| ' + ' | '.join(encabezado) + ' |', '|' + '---|' * len(encabezado)]
    return '\n'.join(lineas + ['| ' + ' | '.join(str(c) for c in f) + ' |' for f in filas])


class Informe:
    def __init__(self, nombre_historico, nombre_revisado, fase):
        self.ruta = ANALISIS / nombre_historico
        self.salida = SALIDA / nombre_revisado
        self.fase = fase
        self.texto = self.ruta.read_text(encoding='utf-8')

    def cambiar(self, viejo, nuevo, seccion, hallazgo, tipo='Corrección'):
        veces = self.texto.count(viejo)
        if veces != 1:
            raise SystemExit(f'{self.ruta.name}: el anclaje aparece {veces} veces: {viejo[:80]!r}')
        self.texto = self.texto.replace(viejo, nuevo)
        BITACORA.append({'informe_historico': f'analisis/{self.ruta.name}', 'informe_revisado': self.salida.relative_to(RAIZ).as_posix(),
                         'seccion': seccion, 'hallazgo': hallazgo, 'tipo': tipo, 'texto_historico': viejo[:300].replace('\n', ' '),
                         'texto_revisado': nuevo[:300].replace('\n', ' ')})

    def agregar_despues(self, ancla, nota, seccion, hallazgo):
        self.cambiar(ancla, f'{ancla}\n\n{nota}', seccion, hallazgo, 'Nota agregada')

    def agregar_antes(self, ancla, nota, seccion, hallazgo):
        self.cambiar(ancla, f'{nota}\n\n{ancla}', seccion, hallazgo, 'Nota agregada')

    def portada(self, cambios):
        titulo, resto = self.texto.split('\n', 1)
        aviso = (f'> **Versión revisada del 04-11-2026, corrección controlada de la Fase 34.** Original conservado sin cambios: '
                 f'`analisis/{self.ruta.name}`. Solo cambian textos y notas; no se volvió a ejecutar ningún análisis y los resultados '
                 f'históricos se conservan. Cada cambio lleva la marca **[Revisión H..]**, con el número de la matriz de hallazgos. '
                 f'Cambios principales: {cambios}')
        self.texto = f'{titulo}\n\n{aviso}\n{resto}'

    def enlaces(self):
        """Las figuras siguen en su carpeta histórica; 34D usa la revisada si existe."""
        def cambiar(m):
            ruta = m.group(2)
            nombre = Path(ruta).name
            if ruta.startswith('figuras/eda_univariado/') and (FIG_REVISADAS / nombre).exists():
                return f'{m.group(1)}(../figuras_34D_revisadas/{nombre})'
            return f'{m.group(1)}(../../{ruta})'
        self.texto = re.sub(r'(!\[[^\]]*\])\((figuras/[^)]+)\)', cambiar, self.texto)

    def guardar(self):
        self.enlaces()
        self.salida.write_text(self.texto, encoding='utf-8')


# ------------------------------------------------------------------------------- 34B

def informe_34B():
    r = Informe('informe_limpieza_usuaria.md', 'informe_limpieza_usuaria_revisado.md', '34B')
    origen = leer('origen_respuestas_34D').set_index('variable')
    claves = ['trabaja_actualmente', 'cuida_otras_personas', 'cantidad_personas_cuida', 'sobrecarga_fisica_emocional',
              'lugar_trabajo_comprensivo', 'estres_entorno_laboral', 'usa_medicamentos_diabetes']
    filas = [[f'`{v}`', origen.at[v, 'observadas'], origen.at[v, 'deducidas'], origen.at[v, 'imputadas'], origen.at[v, 'faltantes'],
              origen.at[v, 'no_aplica']] for v in claves]
    assert origen.at['trabaja_actualmente', 'imputadas'] == 22 and origen.at['cuida_otras_personas', 'imputadas'] == 21
    r.agregar_despues(
        'Las 19 variables restantes no tienen faltantes reales.',
        '### 3.1 Cuatro situaciones distintas de una celda **[Revisión H02, H03, H04, H11]**\n\n'
        'El conjunto limpio no siempre permite distinguir de dónde viene un valor: la marca `<variable>_imputado` solo existe cuando '
        'el faltante alcanza el 5 %. Por eso `trabaja_actualmente` (4,0 %) y `cuida_otras_personas` (3,8 %) no tienen marca. '
        'Esta sección separa las cuatro situaciones:\n\n'
        + tabla(['Situación', 'Qué significa', 'Paso de la limpieza'], [
            ['Respuesta observada', 'La participante respondió. Puede haberse corregido el formato o el código, no el contenido.', '1 a 7'],
            ['Respuesta deducida', 'Venía vacía, pero respondió una pregunta que solo se muestra con cierto valor: ese valor es una conclusión lógica.', '8'],
            ['Respuesta imputada', 'Venía vacía y recibió la moda o la mediana. Es una estimación, no una respuesta.', '9'],
            ['No aplica', 'La encuesta no habría mostrado la pregunta. Queda vacía y no cuenta como faltante.', '8'],
        ]) + '\n\nUn vacío que aplica y no se imputa queda como **faltante real**: por ejemplo, peso y talla, o las preguntas de '
        'menstruación sin fecha de última menstruación.\n\n'
        'Recuento exacto entre las 529 participantes con MRS completo, con el denominador de cada variable:\n\n'
        + tabla(['Variable', 'Observadas', 'Deducidas', 'Imputadas', 'Faltantes reales', 'No aplica'], filas)
        + '\n\nEl detalle de las 71 variables descritas en la 34D está en `tablas/origen_respuestas_34D.csv`, y el indicador por '
        'participante, solo para auditoría, en `tablas/indicadores_auditoria.csv`. Esos indicadores no son variables de análisis.\n\n'
        '### 3.2 Las 22 imputaciones de trabajo y las 21 de cuidado **[Revisión H02, H03, H04]**\n\n'
        '**`trabaja_actualmente`.** 22 respuestas vacías recibieron la moda, «Sí». Estas 22 participantes no respondieron la sección '
        'Trabajo. Entre las 529 quedan 309 clasificadas como trabajadoras: 287 con situación laboral respondida o deducida (286 y 1) y 22 imputadas.\n\n'
        '**`cuida_otras_personas`.** 21 respuestas vacías recibieron la moda, «No». Otras 4 se dedujeron porque esas participantes '
        'respondieron preguntas de cuidado.\n\n'
        '**Efecto sobre `cantidad_personas_cuida`.** Las 21 con «No» imputado quedan como «no aplica» en la limpieza y como 0 en las '
        'codificaciones de la 34C y la 35A. Aparte, 7 cuidadoras con cantidad vacía recibieron la mediana. Son dos grupos distintos.\n\n'
        '**Efecto sobre `doble_carga`.** Esta columna derivada depende de una imputada en 43 filas: 22 por trabajo (10 valen 1 y 12 valen 0) '
        'y 21 por cuidado (todas valen 0). Ninguna fila tiene ambas imputadas. La variable sigue excluida del conjunto vigente de 33.\n\n'
        '**Efecto sobre las poblaciones.** Las poblaciones de 287 y 239 usadas en la Fase 35 solo contienen casos verdaderos según el simulador, '
        'pero están incompletas: faltan 10 trabajadoras y 14 cuidadoras cuya respuesta se perdió. No están mal definidas.\n\n'
        '**Sensibilidad descriptiva.** Quitar las imputadas casi no cambia la asociación con la severidad: `trabaja_actualmente`, rho 0,102 '
        'con las 529 y 0,104 sin las 22; `cantidad_personas_cuida`, rho 0,016 y 0,018. Detalle en `tablas/sensibilidad_asociaciones.csv`.\n\n'
        '**Uso de la verdad del simulador.** Comparado con el simulador, 12 de las 22 imputaciones de trabajo y 14 de las 21 de cuidado no '
        'coinciden, y `doble_carga` difiere en 9 filas. Es una evaluación de la simulación. Ningún valor imputado se reemplazó por el '
        'verdadero, ni debe reemplazarse: en un estudio real ese dato no existiría.',
        '3', 'H02, H03, H04, H11')
    r.agregar_despues(
        'Inventar el peso de tantas participantes cambiaría justamente el factor más fuerte.',
        '**[Revisión H15]** Esta era la decisión de la limpieza. Desde la reunión del 27-10-2026, la Fase 35A imputa el IMC numérico con la media '
        'de las observadas (29,23 kg/m²) y deja la marca `imc_fue_imputado`. Esa decisión posterior no cambia el conjunto limpio.',
        '3', 'H15')
    r.cambiar(
        'Se revisaron 65353 celdas que venían bien; la limpieza cambió por error **1** (0.0 %).\n\n'
        '| Variable | Celdas | Ejemplo | Motivo |\n|---|---|---|---|\n'
        '| cambio_relacion_pareja_menopausia | 196 | 1 → (vacío) | regla del análisis: "no aplica" sin pareja (la plataforma la muestra a todas) |\n'
        '| circunferencia_cintura_cm | 1 | 75 → (vacío) |  |',
        '**[Revisión H16]** Se revisaron 65353 celdas que venían bien. La limpieza cambió 197, por dos razones que no deben sumarse como errores:\n\n'
        + tabla(['Clase', 'Variable', 'Celdas', 'Ejemplo', 'Explicación'], [
            ['Error de limpieza', '`circunferencia_cintura_cm`', 1, '75 → (vacío)', 'Una celda correcta se alteró por error (0,0 % de las revisadas). Esta variable no entra al análisis de la usuaria común.'],
            ['Regla intencional de aplicabilidad', '`cambio_relacion_pareja_menopausia`', 196, '1 → (vacío)', 'Sin pareja, la pregunta se considera «no aplica» (regla propia del análisis; la plataforma la muestra a todas).'],
        ]) + '\n\nHubo **1 error de limpieza**, no 197. Las otras 196 celdas responden a una decisión documentada en la sección 5.',
        '6.3', 'H16')
    r.portada('secciones 3.1 y 3.2 nuevas (observadas, deducidas, imputadas y no aplicables; imputaciones de trabajo y cuidado) y sección 6.3 corregida (1 error y 196 celdas por regla).')
    r.guardar()


# ------------------------------------------------------------------------------- 34C

def seccion_correcciones_34C():
    d = leer('diabetes_pruebas').iloc[0]
    tc = leer('imc_pruebas')
    cat = leer('imc_categorias').set_index('grupo')
    falt = leer('imc_faltante_descriptivo').set_index('grupo')
    sens = leer('sensibilidad_asociaciones')
    assert round(d['rho_severidad_4'], 3) == 0.129 and round(tc.iloc[1]['q_familia_41'], 3) == 0.038

    def fila_sens(v, e):
        return sens[(sens['variable'] == v) & (sens['escenario'] == e)].iloc[0]

    et = ['Original 34C: incluye «no informado»; bajo peso queda fuera', 'Solo observado, 3 categorías; bajo peso queda fuera',
          'Solo observado, 4 categorías, con bajo peso (n = 2)', 'Solo observado, bajo peso unido a normal',
          'Solo observado, categorías ordenadas', 'IMC numérico observado (ya estaba en 34C)']
    ima = []
    for i, f in enumerate(tc.itertuples()):
        origen = 'q oficial de la 34C' if i in (0, 5) else 'q por reemplazo'
        ima.append([et[i], f.prueba, f.n, f'{f.medida} = {n3(f.efecto)}', pv(f.p_sin_ajustar), n3(f.q_familia_41), origen])
    grupos = [[g.capitalize(), int(cat.at[g, 'n']), f'{n1(cat.at[g, "severas_pct"])} %', n1(cat.at[g, 'mrs_media'])]
              for g in ['bajo peso', 'normal', 'sobrepeso', 'obesidad', 'no informado']]
    s529 = fila_sens('sobrecarga_fisica_emocional', 'Actual (0 si no cuida)')
    s251 = fila_sens('sobrecarga_fisica_emocional', 'Solo cuidadoras (251)')
    s239 = fila_sens('sobrecarga_fisica_emocional', 'Solo cuidadoras con respuesta observada')
    c529 = fila_sens('cantidad_personas_cuida', 'Actual (0 si no cuida)')
    c251 = fila_sens('cantidad_personas_cuida', 'Solo cuidadoras (251)')
    return f'''### 6.2.A Notas de revisión sobre estos resultados

Estas notas no cambian la figura de asociaciones ni sus coeficientes. Los resultados históricos siguen siendo los de las tablas anteriores.

#### Medicamentos para la diabetes **[Revisión H01]**

La variable se mantiene en los resultados históricos del EDA:

{tabla(['Respuesta', 'n', 'Síntomas severos', 'MRS medio'], [['Sí', 66, '66,7 %', '20,5'], ['No', 463, '51,2 %', '15,8']])}

- Spearman: rho = +{n3(d['rho_severidad_4'])}, p = {n3(d['p_sin_ajustar'])}, q = {n3(d['q_familia_41'])}. La asociación es **débil, aunque significativa** con el criterio FDR de este EDA.
- Solo con las 506 respuestas observadas: rho = +0,131 y q por reemplazo = 0,022. Las 23 imputadas no explican el resultado.
- La categoría «No» reúne el 87,5 % de las respuestas (87,0 % solo entre observadas): la dominancia supera el 85 %.
- Por decisión metodológica posterior, la variable **no forma parte del conjunto vigente de 33 variables**. Esa exclusión se mantiene.

Las asociaciones de un conjunto sintético, incluida esta, **no constituyen evidencia clínica ni causal**. El simulador programó un efecto para esta variable, de modo que el resultado muestra que el análisis lo detecta, no un hallazgo sobre mujeres reales.

#### IMC por categoría **[Revisión H07, H08]**

El resultado original se conserva, con una limitación: la prueba trató «no informado» como si fuera una cuarta categoría nutricional. Así se mezclan datos faltantes con estado nutricional, y las 262 sin dato diluyen la diferencia entre categorías. La categoría «bajo peso» (n = 2) quedó fuera sin aviso porque la prueba exige al menos 5 casos por grupo: por eso n = 527.

{tabla(['Análisis', 'Prueba', 'n', 'Efecto', 'p', 'q', 'Origen del q'], ima)}

**Cómo leer el q por reemplazo.** Se cambió solo el p de esa prueba dentro de la familia original de 41 y se mantuvieron fijos los otros 40. Es una aproximación descriptiva, **no el resultado oficial de una nueva ejecución completa**. Con ese reemplazo, las pruebas con q < 0,05 pasan de 8 a 9 y ninguna otra variable cambia de lado.

**Lectura.** Separando el dato faltante, la severidad aumenta con el IMC en las observadas. La alternativa directa es la de 3 categorías, porque aplica sin cambios la regla de mínimo 5 casos. Las otras son sensibilidades y no se eligieron por su q. El resultado con 4 categorías (q = {n3(tc.iloc[2]['q_familia_41'])}) muestra que la conclusión depende en parte de cómo se trate a las dos participantes con bajo peso.

{tabla(['Categoría', 'n', 'Síntomas severos', 'MRS medio'], grupos)}

**Bajo peso.** Son dos participantes (IMC 18,2 y 18,4; MRS 12 y 10). Permiten describir, pero no concluir nada sobre esa categoría.

**El dato faltante, como descripción aparte.** Severas: {n1(falt.at['IMC informado', 'severas_pct'])} % con IMC informado (n = {int(falt.at['IMC informado', 'n'])}) y {n1(falt.at['IMC no informado', 'severas_pct'])} % sin informar (n = {int(falt.at['IMC no informado', 'n'])}); ji cuadrado, p = 0,858. No informar el IMC no se relaciona con la severidad, lo que es distinto de tratar «no informado» como un nivel nutricional.

Nada de esto cambia el IMC numérico ni su tratamiento en la Fase 35.

#### Poblaciones **[Revisión H05]**

{tabla(['Población', 'n', 'Qué contiene', 'Dónde se usa'], [
    ['Clasificadas como trabajadoras', 309, '287 con situación laboral respondida o deducida y 22 imputadas', 'Denominador de «quienes trabajan» en 34C y 34D'],
    ['Con situación laboral respondida o deducida', 287, 'Tienen respuestas de la sección Trabajo; en lugar, 16 imputadas y en estrés, 10', 'Shannon y Random Forest laboral'],
    ['Cuidadoras según el conjunto limpio', 251, '239 con sobrecarga observada y 12 con sobrecarga imputada', 'Denominador de 34D'],
    ['Cuidadoras con sobrecarga observada', 239, 'Solo respuestas observadas de sobrecarga', 'Shannon y Random Forest de cuidadoras'],
])}

Las 22 no son «trabajadoras sin responder la sección» en sentido estricto: su propia situación laboral es una estimación. Todas estas cifras son entre las 529 con MRS completo. Sobre las 546 del conjunto limpio, los recuentos de la sección 3 son 320 trabajadoras y 298 con respuestas laborales. Las poblaciones de Shannon y Random Forest no cambian.

#### Por qué la sobrecarga cambia al mirar solo a las cuidadoras **[Revisión H09]**

{tabla(['Base', 'n', 'rho', 'p sin ajustar', 'q'], [
    ['Las 529, con 0 si no cuida', s529['n'], n3(s529['rho']), n3(s529['p_sin_ajustar']), n3(s529['q_familia_41'])],
    ['Cuidadoras', s251['n'], n3(s251['rho']), n3(s251['p_sin_ajustar']), 'no evaluado'],
    ['Cuidadoras con sobrecarga observada', s239['n'], n3(s239['rho']), n3(s239['p_sin_ajustar']), 'no evaluado'],
])}

Son dos preguntas distintas. Con las 529, el coeficiente mezcla «¿cuida o no?» con «¿cuánta sobrecarga siente quien cuida?»: 278 participantes empatan en 0 y, como cuidar casi no se asocia con la severidad (rho = 0,035), ese bloque diluye la relación. Entre cuidadoras queda solo la segunda pregunta.

- **No es un efecto de las imputadas:** rho es prácticamente igual con 251 y con 239 (0,156). La diferencia viene de la codificación con 0.
- **Lo mismo puede pasar con otras variables condicionales.** En cantidad de personas cuidadas, rho = {n3(c529['rho'])} con las 529 y {n3(c251['rho'])} entre cuidadoras (p = {n3(c251['p_sin_ajustar'])}); ninguna es significativa.
- **Los resultados entre cuidadoras son exploratorios:** no pertenecen a la familia de 41 pruebas y no tienen q propio.
- **Shannon responde otra pregunta:** evalúa la sobrecarga en las 239 (SU = 0,020; p = 0,041; q = 0,188) y corrige sobre 33 variables, así que no queda bajo 0,10. No se contradice con este resultado ni cambia.
'''


def informe_34C():
    r = Informe('informe_eda_usuaria.md', 'informe_eda_usuaria_revisado.md', '34C')
    r.agregar_despues(
        'Si se vuelve a ejecutar el script, estos textos deben revisarse.*',
        '*[Revisión H13] El código sigue agrupando la etapa con las variables de control para calcular la prueba. Ese rótulo no cambia el cálculo: '
        'el uso vigente de la etapa es descriptivo. Se actualizaron los textos del generador, pero volver a ejecutar 34C seguiría exigiendo revisar '
        'este informe a mano. Ver el informe de cierre.*',
        'Encabezado', 'H13')
    r.agregar_despues(
        '  no tienen respondida la sección Trabajo.',
        '  **[Revisión H05]** Entre las 529: 309 clasificadas como trabajadoras = 287 con situación laboral respondida o deducida + 22 imputadas. Ver la sección 6.2.A.',
        '1', 'H05')
    r.agregar_antes(
        '**Figura 42. Estrés del entorno laboral**',
        '**[Revisión H05]** En esta sección, «n trabaja = 298» cuenta las respuestas sobre las 546 participantes (320 clasificadas como trabajadoras menos 22 '
        'con situación laboral imputada). Entre las 529 con MRS completo son 287. Las barras no cambian.',
        '3.7', 'H05')
    r.cambiar(
        'No se imputan ni se modelan; el IMC entra como categoría con "no informado".',
        'No se imputan ni se modelan. **[Revisión H07, H15]** En esta fase el IMC entró como categoría con «no informado», lo que mezcla faltantes con estado nutricional (ver 6.2.A). '
        'Desde el 27-10-2026, la Fase 35A imputa el IMC numérico con la media y deja la marca `imc_fue_imputado`.',
        '4.1', 'H07, H15')
    r.cambiar(
        'así que la categoría "no informado" no introduce un sesgo evidente.',
        'así que la categoría "no informado" no introduce un sesgo evidente. **[Revisión H07]** Esto describe el dato faltante; no justifica usar «no informado» como categoría nutricional en la prueba de la sección 6 (ver 6.2.A).',
        '4.3', 'H07')
    r.agregar_despues('| IMC (categoría) | 527 | 0.013 | 0.073 |\n| Etapa menopáusica | 527 | 0.006 | 0.310 |\n| Quién prepara las comidas | 529 | 0.004 | 0.385 |\n| Previsión de salud | 527 | 0.002 | 0.429 |\n| Comuna | 521 | 0.006 | 0.429 |\n| Origen | 523 | -0.001 | 0.667 |\n| Pueblo originario / afro | 521 | -0.002 | 0.702 |\n| Regularidad de la menstruación | 175 | -0.009 | 0.801 |\n| Método anticonceptivo | 68 | -0.005 | 0.801 |',
                      '**[Revisión H07]** El q de 0,073 de `imc_categoria` se conserva como resultado histórico, con la limitación explicada en 6.2.A.', '6.2', 'H07')
    r.agregar_antes('**Salud ginecológica y general.** Se agregan', seccion_correcciones_34C(), '6.2.A', 'H01, H05, H07, H08, H09')
    r.cambiar(
        '- **Medicamentos para la diabetes** (rho = +0.13; p ajustado = 0.020): clase severa 67 % en «Sí» (n = 66) y 51 % en «No» (n = 463).',
        '- **Medicamentos para la diabetes** (rho = +0.13; p ajustado = 0.020): clase severa 67 % en «Sí» (n = 66) y 51 % en «No» (n = 463). **[Revisión H01]** Asociación débil en datos sintéticos, sin valor clínico ni causal; la variable no está en el conjunto vigente de 33 (ver 6.2.A).',
        '7.2', 'H01')
    r.cambiar(
        '- El IMC entra como categoría con "no informado"; el IMC numérico solo sirve en quienes lo informaron.',
        '- El IMC entra como categoría con "no informado"; el IMC numérico solo sirve en quienes lo informaron. **[Revisión H15]** Esta salida quedó superada: la Fase 35A usa el IMC numérico, imputado con la media (decisión del 27-10-2026).',
        '9', 'H15')
    r.portada('sección 6.2.A nueva (diabetes, IMC complementario, poblaciones de 309/287/251/239 y sobrecarga). El q histórico del IMC, 0,073, se conserva.')
    r.guardar()


# ------------------------------------------------------------------------------- 34D

def informe_34D():
    r = Informe('informe_eda_univariado.md', 'informe_eda_univariado_revisado.md', '34D')
    origen = leer('origen_respuestas_34D')
    etiquetas = pd.read_csv(ANALISIS / 'resultados' / 'usuaria' / 'eda_univariado_resumen.csv', encoding='utf-8-sig').set_index('variable')['etiqueta']
    filas = [[etiquetas[f.variable], f.n_valido, f.observadas, f.deducidas, f.imputadas, f.faltantes, f.no_aplica,
              f.dependen_de_imputada if f.derivada else '—'] for f in origen.itertuples()]
    cuentas = leer('auditoria_figuras_34D')
    distintos = cuentas[cuentas['imputados_34B_resumen'] != cuentas['imputadas_exactas_529']]
    tabla_cota = tabla(['Variable', 'imputados_34B histórico', 'Exacto entre las 529'],
                       [[f'`{f.variable}`', f.imputados_34B_resumen, f.imputadas_exactas_529] for f in distintos.itertuples()])
    tramo = cuentas[cuentas['cambia_tramo_80_85']]
    con = cuentas[cuentas['imputadas_exactas_529'] > 0]
    assert (len(cuentas), len(con), int((con['faltante_figura'] == 0).sum()), len(distintos)) == (65, 46, 41, 9)
    r.cambiar(
        '- **Sin imputar.** Los gráficos muestran los datos tal como quedaron tras la limpieza; no se agrega ninguna imputación nueva.',
        '- **Sin imputaciones nuevas.** **[Revisión H10]** Los gráficos muestran los datos tal como quedaron tras la limpieza, que ya incluyen las imputaciones de la Fase 34B. Esta fase no agrega ninguna.',
        '1', 'H10')
    r.agregar_despues(
        '(`pct_dominante_sin_imputados_34B`) y el comentario avisa si cambia de tramo.',
        '- **[Revisión H10, H11] Qué significa «n válido».** Incluye respuestas observadas, deducidas e imputadas. Las figuras históricas mostraban solo «n válido» y «faltante»: en 41 de las 46 variables con imputadas decían «faltante = 0», correcto como cálculo pero incompleto como descripción. Las figuras de esta versión, en `figuras_34D_revisadas/`, separan observadas, deducidas, imputadas, faltantes reales y no aplicables. Las barras y sus porcentajes no cambian.',
        '1', 'H10, H11')
    r.agregar_despues(
        'les correspondía responder.',
        '**[Revisión H05]** En lugar de trabajo y estrés, las 22 faltantes tienen imputada la situación laboral: no se sabe si les correspondía responder. Esas preguntas tienen 287 respuestas válidas: en lugar, 271 observadas y 16 imputadas; en estrés, 277 y 10.\n\n'
        '### 3.1 Origen de las respuestas de cada figura **[Revisión H10]**\n\n'
        'Entre las 529 participantes con MRS completo. En las variables derivadas no hay respuestas propias: la última columna indica cuántas se calcularon con una entrada imputada.\n\n'
        + tabla(['Variable', 'n válido', 'Observadas', 'Deducidas', 'Imputadas', 'Faltantes reales', 'No aplica', 'Derivada: dependen de imputada'], filas)
        + '\n\n**Sobrecarga.** n = 251 cuidadoras: 239 respuestas observadas y 12 imputadas. Las 12 recibieron la mediana y están en «A veces», por lo que esa barra (106) son 94 observadas más 12 imputadas.\n\n'
        '### 3.2 Correcciones al recuento de imputados **[Revisión H11]**\n\n'
        'La columna `imputados_34B` del resumen histórico es una cota contada sobre las 546 cuando la variable no tiene marca `_imputado`. Difiere del recuento exacto en 9 variables:\n\n'
        + tabla_cota + '\n\nEl CSV histórico no se modifica; el recuento exacto está en `tablas/auditoria_figuras_34D.csv`.\n\n'
        f'**Tramos de dominancia.** Sin imputadas, {len(tramo)} variables bajan del 80 %: operada para no tener más hijos, ejercicio aeróbico y platos de verduras. Ninguna cruza el 85 %, de modo que no cambia ninguna decisión de eliminación.',
        '3', 'H05, H10, H11')
    r.cambiar(
        'Se calculan sobre los valores observados, sin imputados (peso, talla e IMC solo de quienes los informaron).',
        '**[Revisión A1]** Se calculan sobre los valores disponibles tras la limpieza: en peso, talla e IMC, solo de quienes los informaron. En horas sentada se **incluyen 27 valores imputados con la mediana (6)**, a diferencia de lo que decía esta frase. Sus cifras históricas no se recalcularon; la figura revisada lo indica en su título.',
        '4', 'A1')
    r.portada('sección 3.1 nueva con el origen de las respuestas de las 71 variables, figuras con rótulo corregido y aclaración sobre horas sentada. Porcentajes y barras no cambian.')
    r.guardar()


# ------------------------------------------------------------------------------- 34E

def informe_34E():
    r = Informe('informe_eda_multivariado.md', 'informe_eda_multivariado_revisado.md', '34E')
    r.agregar_despues(
        'desde el ajuste de la Fase 35A, el modelado usa 35.*',
        '*[Revisión H14] Tres listas distintas, sin que ninguna reemplace los resultados de esta fase: **38 variables exploratorias** (esta matriz histórica); **35 predictoras** (versión previa de la Fase 35A, las 38 menos etapa menopáusica, tipo de sangrado y uso de método anticonceptivo); **33 variables elegibles vigentes** (las 35 menos previsión, doble carga y medicamentos para la diabetes, más sobrecarga de cuidados: 30 generales, 2 laborales y 1 de sobrecarga). La etapa menopáusica es hoy solo descriptiva.*',
        'Encabezado', 'H14')
    r.cambiar('Esta lista no es la del modelado: las predictoras son 35 (Fase 35A).',
              'Esta lista no es la del modelado: las predictoras eran 35 en la versión previa de la Fase 35A y hoy son 33 las variables elegibles **[Revisión H14]**.', '2', 'H14')
    r.cambiar(
        '- **Sin imputaciones.** Se usa lo que las participantes respondieron:',
        '- **Sin imputaciones nuevas en esta fase, pero con las de la limpieza.** **[Revisión H12]** El conjunto de entrada (`dataset_fase35.csv`) conserva las imputaciones de la Fase 34B en las variables generales, por lo que no toda celda es una respuesta observada. Solo se retiran dos imputaciones de la 35A:',
        '2', 'H12')
    r.cambiar(
        '  - **Respuestas laborales originales.** Las 22 trabajadoras sin respuesta en la sección Trabajo, imputadas por mediana en la 35A, quedan fuera de esos pares.',
        '  - **Lugar y estrés laboral.** **[Revisión H05, H12]** Las 22 participantes con situación laboral imputada recibieron un valor por mediana en la 35A y quedan fuera de esos pares; no son trabajadoras confirmadas, porque su «sí» también es una estimación. Los pares usan a las 287 restantes, que incluyen 16 valores de lugar y 10 de estrés imputados en la 34B: no son solo respuestas originales.',
        '2', 'H05, H12')
    r.agregar_despues(
        '*El título dentro de la imagen dice "38 predictoras" porque es la figura original del 30-10-2026, que no se regeneró; hoy deben leerse como variables exploratorias.*',
        '*[Revisión H14] La figura histórica no se regeneró en esta corrección. Doble carga, previsión y medicamentos para la diabetes aparecen en ella porque es exploratoria, no porque sigan siendo elegibles.*',
        '3', 'H14')
    r.cambiar('Estos grupos se calcularon sobre las 38 variables exploratorias, así que para el modelado, que usa 35 predictoras, son solo una orientación.',
              'Estos grupos se calcularon sobre las 38 variables exploratorias, así que para el modelado, que hoy parte de 33 variables elegibles **[Revisión H14]**, son solo una orientación.', '6', 'H14')
    r.portada('frase «Sin imputaciones» corregida, aclaración sobre las 22 y distinción entre 38, 35 y 33 variables. Matrices, grupos y modelos no cambian.')
    r.guardar()


def main():
    SALIDA.mkdir(exist_ok=True)
    informe_34B()
    informe_34C()
    informe_34D()
    informe_34E()
    pd.DataFrame(BITACORA).to_csv(TABLAS / 'relacion_correcciones.csv', index=False, encoding='utf-8-sig')
    print(len(BITACORA), 'cambios registrados')


if __name__ == '__main__':
    main()
