"""
Cierre de las Fases 34 y 35: tablas de estado, limitaciones y archivos. Solo escribe en cierre_fases_34_35/tablas/.
Uso, desde analisis/: python cierre_fases_34_35/scripts/generar_tablas_cierre.py
"""
import csv
import json
from pathlib import Path

ANALISIS = Path(__file__).resolve().parents[2]
RAIZ = ANALISIS.parent
CIERRE = ANALISIS / 'cierre_fases_34_35'
TABLAS = CIERRE / 'tablas'
HALLAZGOS = ANALISIS / 'revision_correctiva_fase34' / 'tablas' / 'hallazgos_antes_despues.csv'

H11_H13 = [
    {'hallazgo': 'H11', 'estado_definitivo': 'Resuelto en el código',
     'problema': 'imputados_34B contaba sobre 546 participantes cuando la variable no tenía marca _imputado. Era una cota que difería del valor exacto en 9 variables, entre 1 y 3 celdas.',
     'ubicacion': 'analisis/eda/univariado.py: bloque de describir(), ahora recuento_imputados()',
     'correccion': 'Orden del recuento: 1) marca de la fila, 2) tabla de origen si su n válido coincide, 3) cota del diccionario, solo si faltan los anteriores.',
     'sin_cambio': 'Frecuencias, n, porcentajes, entropía, forma y comentarios. Las tablas históricas tampoco se tocaron.',
     'pruebas': '14 de 14 correctas: 5 de regla y 9 en memoria con los datos reales (65 variables iguales a la auditoría; solo cambian las 9).',
     'alcance_pendiente': 'El CSV histórico conserva la cota; los valores exactos están en tablas/h11_nueve_variables.csv. Depende de origen_respuestas_34D.csv. pct_dominante_sin_imputados_34B sigue siendo una cota inferior: supone que todas las imputadas cayeron en la categoría dominante.'},
    {'hallazgo': 'H13', 'estado_definitivo': 'Resuelto en rótulos y metadatos',
     'problema': 'Al volver a ejecutar el script, etapa_menopausica recibiría el rol «control» y la sección 3.1 perdería la mención descriptiva.',
     'ubicacion': 'analisis/eda_usuaria.py: ROLES_DESCRIPTIVOS, rotular_roles(), TITULOS_INFORME',
     'correccion': 'Rótulo de salida «descriptiva» aplicado después de la corrección FDR; título de la sección 3.1 alineado con el informe histórico.',
     'sin_cambio': 'Composición de V.CONTROL_USUARIA y de las familias FDR, orden de las pruebas, efecto, p y q. La etapa sigue fuera de las elegibles.',
     'pruebas': '7 de 7 correctas: 2 de regla y 5 en memoria con los datos reales (roles iguales al CSV histórico en todas las filas; estadísticos iguales).',
     'alcance_pendiente': 'Internamente la etapa sigue agrupada en V.CONTROL_USUARIA y BLOQUES["control"]. Sacarla de ahí alteraría el flujo, por lo que no se hizo. La figura 89 conserva «Variables de control» porque no incluye la etapa.'},
]

LIMITACIONES = [
    ('L01', 'H14', 'Fase 34E', 'La figura histórica de 34E dice «38 predictoras»; hoy hay 33 elegibles.', 'Regenerarla exige ejecutar el análisis multivariado completo.', 'Solo de lectura de la figura; el texto revisado aclara 38, 35 y 33.', 'Abierta y documentada'),
    ('L02', 'H17', 'Random Forest', 'La sensibilidad de Random Forest identificó imputadas por celdas vacías del conjunto sucio y encontró menos en 10 variables.', 'Medir su efecto exige nueva sensibilidad de Random Forest.', 'Efecto sin medir; afecta sobre todo a cantidad de personas que cuida (6 de 7).', 'Abierta y documentada'),
    ('L03', 'A1', 'Fase 34D', 'La asimetría y la curtosis de horas sentada incluyen 27 valores imputados.', 'Corregirlas exige recalcular estadísticos históricos.', 'Se corrigieron título y texto, no las cifras.', 'Abierta y documentada'),
    ('L04', 'Sensibilidad', 'Shannon', 'No existe la sensibilidad de Shannon sin imputaciones laborales.', 'Exige nuevas permutaciones.', 'Sin medir; trabaja_actualmente (q = 0,089) incluye las 22 imputadas.', 'Abierta y documentada'),
    ('L05', 'H06', 'Fase 35', 'Las 22 tienen lugar = 3 y estrés = 3 en los conjuntos de la Fase 35.', 'Los conjuntos no se modifican.', 'Shannon y Random Forest laboral usaron 287, así que esos valores no entraron. El protocolo de la Fase 36 los deja fuera del módulo laboral.', 'Decisión tomada; datos intactos'),
    ('L06', 'H02, H03, H04', 'Fases 34B y 35', 'Imputaciones de situación laboral (22) y de cuidado (21), de las que depende doble carga (43 filas).', 'Cambiarlas exige repetir la limpieza.', 'Rho casi igual en la auditoría; doble carga sigue fuera de las elegibles.', 'Conservada y documentada'),
    ('L07', 'IMC', 'Fases 35A y 36', 'IMC imputado por la media en 262 de 529 (49,5 %).', 'Decisión metodológica vigente.', 'Rho baja de 0,250 a 0,192; con observados, n = 267, SU = 0,0284 y q de reemplazo = 0,0673.', 'Comparación con y sin IMC planificada para los perfiles'),
    ('L08', 'H11', 'Fase 34D', 'eda_univariado_resumen.csv conserva la cota en 9 variables.', 'El archivo histórico no se sobrescribe.', 'Valores exactos en tablas/h11_nueve_variables.csv; ninguna cambia de tramo.', 'Código resuelto; histórico conservado'),
    ('L09', 'Reejecución', 'Fases 34C y 34D', 'eda_univariado.py borra figuras al ejecutarse; eda_usuaria.py regenera informes y figuras históricos.', 'Cambiar ese flujo excede este cierre.', 'No se ejecutaron. Volver a ejecutarlos exige copia previa o carpeta aislada.', 'Riesgo documentado'),
    ('L10', 'Rótulos 34C', 'Fase 34C', 'Las figuras históricas de 34C muestran «n trabaja» con imputadas (por ejemplo, 320 sobre 546).', 'Las figuras históricas no se sobrescriben.', 'Aclarado en los informes revisados.', 'Abierta y documentada'),
    ('L11', 'Criterio q', 'Shannon', 'q < 0,10 es un criterio exploratorio adoptado después del oficial (5.000 permutaciones y q < 0,05, sin seleccionadas).', 'Decisión registrada; no se cambia.', 'Con 10.000 ninguna q < 0,05; con 50.000, dos, y el intervalo Monte Carlo de días de ejercicio cruza 0,05.', 'Limitación de interpretación'),
    ('L12', 'Datos', 'Todas', 'Los datos son sintéticos y contienen relaciones programadas.', 'Propio del diseño.', 'Los hallazgos validan el procedimiento, no describen a una población real.', 'Limitación permanente'),
    ('L13', 'Sobreajuste', 'Random Forest', 'ROC-AUC de entrenamiento entre 0,796 y 0,987 frente a evaluación entre 0,538 y 0,659.', 'No se reentrena.', 'Capacidad predictiva modesta.', 'Limitación de interpretación'),
    ('L14', 'Subpoblaciones', 'Shannon y Random Forest', 'Módulos con 287 y 239 participantes; las pruebas tienen menos potencia que con 529.', 'Tamaños fijados por la encuesta.', 'C1 frente a C0 y D1 frente a D0 sin diferencia clara.', 'Limitación de interpretación'),
    ('L15', 'Causalidad', 'Shannon, FCBF y Random Forest', 'SU e importancia predictiva no demuestran causalidad; SU tampoco indica dirección.', 'Propio de los métodos.', 'La dirección se informa por separado y solo como descripción.', 'Limitación permanente'),
    ('L16', 'Etapa', 'Fases 34 y 35', 'La regla de etapa menopáusica es una aproximación propia y no está validada.', 'Decisión de la responsable del proyecto.', 'Solo descriptiva; fuera de las elegibles.', 'Abierta y documentada'),
    ('L17', 'Archivo 33', 'Fase 36', 'dataset_fase35_33_variables.csv trae prevision y doble_carga, y no trae sobrecarga.', 'Los conjuntos no se modifican.', 'La Fase 36 debe armar su entrada con la lista de 33, sin usar todas las columnas del archivo.', 'Condición para la Fase 36'),
    ('L18', 'Reproducción', 'Fase 35B', 'complementario_fase35b.py exige HEAD 745d689 y árbol versionado limpio: hoy se detendría, y también después de un commit.', 'Protección del propio script.', 'No afecta los resultados guardados.', 'Riesgo documentado'),
]

# Estado definitivo: solo se reemplaza lo que este cierre cambia o precisa frente a la tabla anterior.
ESTADO_NUEVO = {
    'H06': 'Decisión tomada para la Fase 36; datos intactos',
    'H11': 'Resuelto en el código; CSV histórico conservado',
    'H13': 'Resuelto en rótulos y metadatos',
    'H14': 'Limitación abierta: texto aclarado, figura histórica sin regenerar',
    'H17': 'Limitación abierta: documentada, efecto sin medir',
    'A1': 'Limitación abierta: título y texto corregidos; asimetría y curtosis sin recalcular',
}

BASE = 'analisis/cierre_fases_34_35'
CREADOS = [
    (f'{BASE}/informes/informe_cierre_fase34_v2.docx', 'Cierre actualizado de la Fase 34'),
    (f'{BASE}/informes/informe_cierre_fase35.docx', 'Cierre formal de la Fase 35'),
    (f'{BASE}/informes/informe_preprocesamiento_fase35_revisado.md', 'Versión documental revisada de 35A'),
    (f'{BASE}/informes/protocolo_trabajo_fase36.docx', 'Protocolo de trabajo para la Fase 36'),
    (f'{BASE}/informes/resumen_ejecutivo_cierre.docx', 'Resumen ejecutivo del cierre conjunto'),
    (f'{BASE}/tablas/estado_h11_h13.csv', 'Estado de H11 y H13'),
    (f'{BASE}/tablas/h11_nueve_variables.csv', 'Cota histórica y valor exacto en las 9 variables'),
    (f'{BASE}/tablas/hallazgos_estado_definitivo.csv', 'Estado definitivo de los 18 hallazgos'),
    (f'{BASE}/tablas/registro_limitaciones.csv', 'Limitaciones que permanecen'),
    (f'{BASE}/tablas/archivos_creados_y_modificados.csv', 'Esta tabla'),
    (f'{BASE}/tablas/verificacion_integridad_posterior.csv', 'Comprobaciones finales de integridad'),
    (f'{BASE}/tablas/cambios_detectados.csv', 'Cambios frente a cada manifiesto'),
    (f'{BASE}/tablas/verificacion_fase35.csv', 'Cifras de la Fase 35 contra los archivos'),
    (f'{BASE}/tablas/registro_pruebas.csv', 'Pruebas ejecutadas y no ejecutadas'),
    (f'{BASE}/tablas/datos_fase35.json', 'Cifras leídas para los informes'),
    (f'{BASE}/tablas/integridad.json', 'Resumen de integridad para los informes'),
    (f'{BASE}/tablas/pruebas.json', 'Resumen de pruebas para los informes'),
    (f'{BASE}/tablas/tablas_cierre.json', 'Tablas para los informes'),
    (f'{BASE}/integridad/manifiesto_antes.csv', 'Huella SHA-256 antes del cierre'),
    (f'{BASE}/integridad/manifiesto_despues.csv', 'Huella SHA-256 después del cierre'),
    (f'{BASE}/integridad/git_antes.txt', 'Estado de git antes del cierre'),
    (f'{BASE}/integridad/git_despues.txt', 'Estado de git después del cierre'),
    (f'{BASE}/scripts/manifiesto_cierre.py', 'Genera los manifiestos'),
    (f'{BASE}/scripts/verificar_integridad_cierre.py', 'Compara los manifiestos'),
    (f'{BASE}/scripts/verificar_fase35.py', 'Verifica las cifras de la Fase 35'),
    (f'{BASE}/scripts/generar_35A_revisado.py', 'Genera la versión revisada de 35A'),
    (f'{BASE}/scripts/generar_tablas_cierre.py', 'Genera estas tablas'),
    (f'{BASE}/scripts/ejecutar_pruebas.py', 'Ejecuta y registra las pruebas'),
    (f'{BASE}/scripts/test_h11_h13.py', 'Pruebas de H11 y H13'),
    (f'{BASE}/scripts/test_documental_cierre.py', 'Pruebas documentales y de las 33 variables'),
    (f'{BASE}/scripts/word_comun.js', 'Funciones comunes de Word'),
    (f'{BASE}/scripts/generar_informes_cierre.js', 'Genera los cuatro documentos Word'),
]
MODIFICADOS_NUEVOS = [
    ('analisis/eda/univariado.py', 'H11: nueva función recuento_imputados(), usada por describir()'),
    ('analisis/eda_usuaria.py', 'H13: ROLES_DESCRIPTIVOS, TITULOS_INFORME y rotular_roles(); comentario actualizado'),
]
PREVIOS = ['analisis/eda/univariado.py', 'analisis/eda_univariado.py', 'analisis/eda/informe_multivariado.py', 'analisis/eda/multivariado.py',
           'analisis/eda/informe_usuaria.py', 'analisis/eda_usuaria.py', 'analisis/eda/variables.py', 'analisis/limpieza/informe.py']


def escribir(nombre, cabeza, filas):
    with (TABLAS / nombre).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(cabeza)
        w.writerows(filas)


def main():
    TABLAS.mkdir(parents=True, exist_ok=True)
    cab = list(H11_H13[0])
    escribir('estado_h11_h13.csv', cab, [[x[c] for c in cab] for x in H11_H13])
    cab_l = ['id', 'origen', 'fase', 'limitacion', 'por_que_no_se_resuelve', 'efecto_o_tratamiento', 'estado']
    escribir('registro_limitaciones.csv', cab_l, LIMITACIONES)
    with HALLAZGOS.open(encoding='utf-8-sig', newline='') as f:
        hallazgos = list(csv.DictReader(f))
    filas_h = [[h['id'], h['clase'], h['hallazgo'], h['estado_despues'], ESTADO_NUEVO.get(h['id'], h['estado_despues']),
                'Sí' if h['id'] in ESTADO_NUEVO else 'No'] for h in hallazgos]
    escribir('hallazgos_estado_definitivo.csv', ['id', 'clase', 'hallazgo', 'estado_en_cierre_anterior', 'estado_definitivo', 'cambia_en_este_cierre'], filas_h)
    filas_a = [['Creado en este cierre', r, d] for r, d in CREADOS]
    filas_a += [['Modificado en este cierre', r, d] for r, d in MODIFICADOS_NUEVOS]
    filas_a += [['Modificado en la corrección controlada (no atribuible a este cierre)', r, 'Textos, rótulos y comentarios, incluidas las funciones auxiliares que los construyen'] for r in PREVIOS]
    escribir('archivos_creados_y_modificados.csv', ['origen', 'ruta', 'descripcion'], filas_a)
    salida = {'h11_h13': H11_H13, 'limitaciones': [dict(zip(cab_l, x)) for x in LIMITACIONES],
              'hallazgos': [dict(zip(['id', 'clase', 'hallazgo', 'antes', 'definitivo', 'cambia'], x)) for x in filas_h]}
    (TABLAS / 'tablas_cierre.json').write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding='utf-8')
    faltan = [r for r, _ in CREADOS if not (RAIZ / r).exists()]
    print(f'{len(CREADOS)} creados previstos; faltan aún: {faltan}')


if __name__ == '__main__':
    main()
