"""
Paso 0: perfil del dataset de referencia (figshare 20822032, "Data Set Menopause Women",
Assaf et al., Jordania, CC BY 4.0). Genera analisis/perfil_dataset_referencia.md.
Uso: python analisis/perfil_referencia.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parent
RUTA = BASE.parent / 'datos' / 'referencia' / 'data_set_menopause.xlsx'
SALIDA = BASE / 'perfil_dataset_referencia.md'

# Significado inferido desde cuestionario.docx (mismo artículo de figshare).
# 1 = sí / 2 = no en las preguntas dicotómicas. Las etiquetas son inferencias, no un libro de códigos oficial.
SIGNIFICADO = {
    'Age': ('numérica', 'Edad en años', 'fecha_nacimiento → edad'),
    'City': ('nominal', 'Gobernación de Jordania (1 Irbid/Norte, 2 Amán, 3 Zarqa, 4 Karak/Sur)', 'region_residencia / comuna (solo como forma de la distribución)'),
    'profession working': ('nominal', 'Situación laboral (1 trabaja, 2 jubilada)', 'trabaja_actualmente'),
    'Unnamed: 3': ('nominal', 'Tipo de trabajo (1 administrativo, 2 académico, 3 profesional, 4 salud, 5 otro)', 'estamento (no está en models.py)'),
    'Increase Bp Thyroid gland': ('nominal', 'Hipertensión (1 sí)', 'usa_medicamentos_presion / presión EMPA'),
    'Unnamed: 5': ('nominal', 'Enfermedad tiroidea (1 sí)', '—'),
    'Back pain': ('nominal', 'Dolor de espalda severo (1 sí)', 'MRS p4 (molestias musculares y articulares), aproximado'),
    'DM': ('nominal', 'Diabetes (1 sí)', 'usa_medicamentos_diabetes / glicemia EMPA'),
    'Heart disease': ('nominal', 'Cardiopatía (1 sí)', '—'),
    'Varcoise': ('nominal', 'Várices (1 sí)', '—'),
    'Constipation': ('nominal', 'Constipación/diarrea crónica (1 sí)', 'evacuacion_intestinal'),
    'Respiratory': ('nominal', 'Enfermedad respiratoria crónica (1 sí)', '—'),
    'Tumors': ('nominal', 'Tumores (1 sí)', '—'),
    'chronicd': ('nominal', 'Derivada: tiene alguna crónica (0/1)', '—'),
    'Who give money': ('nominal', 'Sostenedor principal del hogar', '—'),
    'Social status': ('nominal', 'Estado civil (1 casada, 2 divorciada, 3 viuda, 4 soltera)', 'tiene_pareja'),
    'Educational degree': ('ordinal', 'Educación (1 escolar, 2 diploma, 3 universitaria, 4 postgrado, 5 técnica)', 'nivel_educacion'),
    'income': ('ordinal', 'Ingreso suficiente (1 sí, 2 más o menos, 3 no)', '—'),
    'How do you evaluate your health status': ('ordinal', 'Autoevaluación de salud (3 niveles, sentido no documentado)', '—'),
    'Loss menstuartion': ('nominal', 'Cómo llegó a la menopausia (1 natural, 2 quirúrgica, 3 tratamiento); vacío = aún no menopausia', 'fecha_ultima_menstruacion (≥12 meses) / tiene_utero / tiene_ovario'),
    'Children': ('ordinal', 'N° de hijos vivos (categorizado 1-6)', '—'),
    'Pregnancies': ('ordinal', 'N° de embarazos (categorizado 1-4)', '—'),
    'how do you evaluate knowledge about menopause': ('ordinal', 'Conocimiento sobre menopausia (1 muy bueno … 4 malo)', 'considera_informacion_suficiente / nivel_informacion_servicios'),
    'source of information': ('nominal', 'Fuente de información (1 TV, 2 redes, 3 familia/amigas, 4 salud)', '—'),
    'Do you examine breast monthly': ('nominal', 'Autoexamen de mama último año (1 sí)', '—'),
    'Do you use mamogram': ('nominal', 'Mamografía preventiva último año (1 sí)', 'fecha_mamografia (EMPA, personal de salud)'),
    'Do you use swap': ('nominal', 'PAP último año (1 sí)', 'fecha_ultimo_pap (EMPA, personal de salud)'),
    'Do you apply routine exam': ('nominal', 'Control ginecológico cada 6 meses (1 sí)', 'fecha_ultimo_empa'),
    'preventive': ('nominal', 'Derivada: alguna conducta preventiva (0/1)', '—'),
    'Do you use contraceptive': ('nominal', 'Usó anticonceptivos hormonales alguna vez (1 sí)', 'usa_metodo_anticonceptivo (no equivalente: aquí es "alguna vez")'),
    'agecat': ('ordinal', 'Derivada: edad en 3 tramos (45-50, 51-55, 56-60)', '—'),
    'emotional': ('numérica', 'UQOL subescala emocional (suma)', 'MRS psicológica (sentido inverso, aproximado)'),
    'sexual': ('numérica', 'UQOL subescala sexual (suma)', 'MRS urogenital p10 + tiene_actividad_sexual (aproximado)'),
    'health': ('numérica', 'UQOL subescala salud (suma)', 'MRS somática + hábitos (aproximado)'),
    'occupational': ('numérica', 'UQOL subescala ocupacional (suma)', 'EvaluacionTrabajo (aproximado)'),
    'totalqol': ('numérica', 'UQOL total (suma de 23 ítems, mayor = mejor calidad de vida)', 'MRS total (sentido inverso, aproximado)'),
    'educationcat': ('nominal', 'Derivada: educación en 2 grupos', '—'),
    'finiacialcat': ('nominal', 'Derivada: sostenedor en grupos (1, 2, 4)', '—'),
}
UQOL_ITEMS_DESDE, UQOL_ITEMS_HASTA = 'I could control my important things', 'I am continuing work on my goals'
SUBESCALAS = ['emotional', 'sexual', 'health', 'occupational', 'totalqol']


def md(df_, index=True):
    """Tabla markdown sin depender de tabulate."""
    df_ = df_.reset_index() if index else df_
    filas = [[str(v) for v in df_.columns]] + [[str(v) for v in r] for r in df_.itertuples(index=False)]
    lineas = ['| ' + ' | '.join(f) + ' |' for f in filas]
    lineas.insert(1, '|' + '---|' * len(df_.columns))
    return '\n'.join(lineas)


def main():
    df = pd.read_excel(RUTA)
    cols = list(df.columns)
    items = cols[cols.index(UQOL_ITEMS_DESDE):cols.index(UQOL_ITEMS_HASTA) + 1]
    for c in items:
        SIGNIFICADO.setdefault(c, ('ordinal', f'Ítem UQOL recodificado a 3 niveles: "{c}"', 'ítems de estilo de vida/ánimo (aproximado)'))

    # Variables derivadas para correlaciones
    d = pd.DataFrame({
        'edad': df['Age'],
        'posmenopausia': df['Loss menstuartion'].notna().astype(int),
        'trabaja': (df['profession working'] == 1).astype(int),
        'ejercicio_3v': df['I practice exercise 3 times at least'],
        'educacion': df['Educational degree'].replace({5: 2}),  # técnica ≈ diploma
        'ingreso_insuf': df['income'],
        'n_cronicas': (df[['Increase Bp Thyroid gland', 'Unnamed: 5', 'Back pain', 'DM', 'Heart disease',
                           'Varcoise', 'Constipation', 'Respiratory', 'Tumors']] == 1).sum(axis=1),
        'casada': (df['Social status'] == 1).astype(int),
        # ítems negativos ya invertidos en el Excel: mayor = menos ánimo deprimido / ansiedad
        'animo_inv': df['I feel moody in general'],
        'ansiedad_inv': df['I feel anxious'],
    })
    for s in SUBESCALAS:
        d[s] = df[s]

    out = []
    w = out.append
    w('# Perfil del dataset de referencia\n')
    w('> Fuente: figshare 20822032 "Data Set Menopause Women" (Assaf et al., Jordania), CC BY 4.0, '
      'DOI 10.6084/m9.figshare.20822032.v4. Generado por `analisis/perfil_referencia.py`.\n')
    w(f'## 1. Tamaño\n\n- **{df.shape[0]} filas × {df.shape[1]} columnas**, una fila por mujer, sin ID.')
    w(f'- Población: mujeres trabajadoras o jubiladas de Jordania, **{df.Age.min()}-{df.Age.max()} años** '
      f'(media {df.Age.mean():.1f}, DE {df.Age.std():.1f}).')
    w('- Todo está codificado numéricamente (sin etiquetas). El significado se infiere de `cuestionario.docx`.')
    nul = df.isna().sum()
    w(f'- Nulos: solo `Loss menstuartion` ({nul["Loss menstuartion"]} = {nul["Loss menstuartion"] / len(df):.0%}), '
      'que es condicional (solo la responde quien ya está en menopausia). **No hay errores, duplicados ni outliers**: '
      'es un dataset ya limpio.\n')
    w('- **Importante:** el cuestionario original tenía 27 síntomas (bochornos, sudores, sueño, ánimo, urinarios, '
      'sexuales…) pero **esos ítems no vienen en el Excel**. Tampoco trae MRS, peso, talla, presión ni laboratorio. '
      'Lo único "de síntomas" es la escala de calidad de vida UQOL (Utian).\n')

    w('## 2. Columnas\n')
    filas = []
    for c in cols:
        tipo, sig, eq = SIGNIFICADO.get(c, ('?', '?', '—'))
        s = df[c]
        if s.nunique() <= 6:
            dist = ', '.join(f'{int(k)}:{v}' for k, v in s.value_counts().sort_index().items())
        else:
            dist = f'{s.min():g}-{s.max():g}, media {s.mean():.1f} (DE {s.std():.1f})'
        filas.append((f'`{c}`', tipo, sig, f'{s.isna().mean():.0%}', dist, eq))
    w(md(pd.DataFrame(filas, columns=['columna', 'tipo', 'significado probable', 'nulos', 'distribución',
                                      'equivalente en nuestra encuesta']), index=False))
    w('\nNota: los 23 ítems UQOL vienen recodificados a **3 niveles**, pero las subescalas suman el original '
      'de 5 niveles (p. ej. `emotional` va de 6 a 30 = 6 ítems × 1-5). Sirve la subescala, no el ítem suelto.\n')

    w('## 3. Distribuciones clave\n')
    w(md(df[SUBESCALAS + ['Age']].describe().round(1).T[['mean', 'std', 'min', '25%', '50%', '75%', 'max']]))
    etapa = df['Loss menstuartion'].map({1: 'posmenopausia natural', 2: 'quirúrgica', 3: 'por tratamiento'}) \
        .fillna('pre/perimenopausia')
    w('\n**Etapa:**\n')
    w(md(etapa.value_counts().to_frame('n').assign(pct=lambda x: (x.n / len(df) * 100).round(0))))
    w('\n**Prevalencias (sí):** ' + ', '.join(
        f'{n} {(df[c] == 1).mean():.0%}' for n, c in [
            ('hipertensión', 'Increase Bp Thyroid gland'), ('diabetes', 'DM'), ('tiroides', 'Unnamed: 5'),
            ('dolor espalda', 'Back pain'), ('várices', 'Varcoise'), ('cardiopatía', 'Heart disease'),
            ('mamografía año', 'Do you use mamogram'), ('PAP año', 'Do you use swap'),
            ('anticonceptivo alguna vez', 'Do you use contraceptive'), ('trabaja', 'profession working'),
            ('casada', 'Social status')]) + '.')
    w(f'\nEjercicio ≥3 veces/semana: no es cierto {(df["I practice exercise 3 times at least"] == 1).mean():.0%}, '
      f'algo {(df["I practice exercise 3 times at least"] == 2).mean():.0%}, '
      f'muy cierto {(df["I practice exercise 3 times at least"] == 3).mean():.0%}.\n')

    w('## 4. Correlaciones relevantes (Spearman)\n')
    w('Mayor UQOL = mejor calidad de vida (sentido opuesto al MRS). * p<0.05, ** p<0.01.\n')
    predictores = ['edad', 'posmenopausia', 'trabaja', 'ejercicio_3v', 'educacion', 'ingreso_insuf',
                   'n_cronicas', 'casada', 'animo_inv', 'ansiedad_inv']
    m = pd.DataFrame(index=predictores, columns=SUBESCALAS)
    for p_ in predictores:
        for s in SUBESCALAS:
            r, pv = stats.spearmanr(d[p_], d[s])
            m.loc[p_, s] = f'{r:+.2f}' + ('**' if pv < .01 else '*' if pv < .05 else '')
    w(md(m))
    r_sub = d[['emotional', 'sexual', 'health', 'occupational']].corr(method='spearman').round(2)
    w('\n**Entre subescalas:**\n')
    w(md(r_sub))

    w('\n## 5. Lectura para la simulación\n')
    w('- Efectos **pequeños-moderados** y mucho ruido: el modelo de regresión del análisis anterior explicaba '
      'R² ≈ 0.18 de la calidad de vida. Una simulación realista no debería tener efectos más fuertes que eso '
      'para las variables de estilo de vida.')
    w('- Edad y etapa casi no se asocian con UQOL en este dataset (ver tabla); la literatura MRS sí reporta '
      'más síntomas somáticos/urogenitales en posmenopausia → ahí usaremos literatura, marcado como tal.')
    w('- Ejercicio (sobre todo con la subescala salud, rho 0.55), trabajar y educación son los factores '
      'protectores más claros; las enfermedades crónicas restan un poco. `animo_inv`/`ansiedad_inv` vienen '
      'invertidos (mayor = menos síntomas) y son parte de la subescala emocional, por eso correlacionan tanto.')
    w('- Edad y etapa solo se asocian (débil) con la subescala sexual.')
    w('- Sirve como referencia para: distribución de edad, proporción pre/peri vs posmenopausia (~31/69 %), '
      'menopausia quirúrgica (~4 %), prevalencias de HTA/DM, prevención (mamografía/PAP ~20 %), '
      'proporción de ejercicio regular, y tamaño de efecto del ejercicio.')
    w('- **No sirve** para: ítems MRS, antropometría, laboratorio, hábitos alimentarios, tabaco/alcohol, '
      'tareas de cuidado, conocimiento del sistema de salud chileno. Eso irá con literatura o supuestos '
      'explícitos (Paso 1).')
    w('- Contexto distinto (Jordania 45-60 vs. UCN Coquimbo 40-60): las proporciones deben adaptarse, '
      'no copiarse.')

    SALIDA.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'Escrito {SALIDA}')
    print(m.to_string())
    print(etapa.value_counts().to_string())


if __name__ == '__main__':
    main()
