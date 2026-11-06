"""
Matriz de impacto de la revisión correctiva de la Fase 34.

Uso, desde la raíz del proyecto, después de auditoria_fase34.py:
    python analisis/revision_correctiva_fase34/matriz_impacto.py

Es texto de diagnóstico: resume los hallazgos, sus cifras salen de tablas/. Escribe solo en tablas/.
También reúne las tablas en tablas/tablas.json para el generador del informe Word.
"""
import csv
import json
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
TABLAS = AQUI / 'tablas'
COLUMNAS = ['id', 'clase', 'hallazgo', 'archivos_variables', 'solo_presentacion', 'calculos_eda', 'datos_poblaciones_f35',
            'recalcular_su_p_q_fcbf', 'repetir_rf', 'correccion_minima']
E, M, D, V = 'Error comprobado', 'Metodológica discutible', 'Documental', 'Verificado sin error'
SI_DECIDE = 'Solo si se decide tratar esas celdas como faltantes'
FILAS = [
    ['H01', V, 'Diabetes: asociación rho +0,13 con 87,5 % de «No». La codificación y el q son correctos.',
     '34C asociacion_severidad.csv; usa_medicamentos_diabetes', 'No', 'No', 'No', 'No', 'No',
     'Ninguna. Se mantiene excluida del modelado por dominancia.'],
    ['H02', M, '22 respuestas de trabajo imputadas como «Sí», sin marca; 12 distintas del simulador. Rho casi igual: 0,102 frente a 0,104.',
     'dataset limpio, dataset_fase35_33_variables.csv; trabaja_actualmente', 'No', 'No cambia la conclusión',
     'Sí en 22 celdas de la columna; no en las poblaciones', f'No. {SI_DECIDE}: SU, p y q de trabaja y BH de las 33; FCBF si cambia la selección',
     f'No. {SI_DECIDE}: A, B, D0, D1 y sus derivados', 'Documentar y conservar los indicadores de auditoría en un archivo aparte.'],
    ['H03', M, '21 respuestas de cuidado imputadas como «No», sin marca; 14 distintas del simulador. Fijan cantidad = 0. Rho casi igual: 0,016 frente a 0,018.',
     'dataset limpio, dataset_fase35_33_variables.csv; cuida_otras_personas, cantidad_personas_cuida', 'No', 'No cambia la conclusión',
     'Sí en 21 celdas de cantidad; no en las poblaciones', f'No; q de cantidad 0,188. {SI_DECIDE}: SU, p y q de cantidad y BH de las 33',
     f'No. {SI_DECIDE}: B, C0, C1, D0, D1 y sus derivados', 'Documentar. Señalar en la tesis que la población de cuidadoras está incompleta, no mal definida.'],
    ['H04', M, 'doble_carga depende de una imputada en 43 filas y difiere del simulador en 9. Sigue fuera de las 33.',
     '34C; versiones históricas E y C de 35B; doble_carga', 'No', 'No cambia la conclusión (q 0,117 y 0,086)', 'No: columna presente, no elegible', 'No', 'No',
     'Documentar. No usar la columna en la Fase 36.'],
    ['H05', E, '«Quienes trabajan» cuenta 309 e incluye las 22 imputadas; las figuras de lugar y estrés dicen «faltante = 22». Solo 287 tienen respuestas laborales.',
     '34C frecuencias; 34D univariado_lugar_*, univariado_estres_*; 34E y 35A («22 trabajadoras»)', 'Sí', 'No', 'No: la Fase 35B ya usa 287', 'No', 'No',
     'Aclarar denominador: 287 con respuesta; 22 sin respuesta y con situación laboral imputada.'],
    ['H06', M, 'Las 22 tienen lugar = 3 y estrés = 3 en el conjunto de la Fase 35; quienes no trabajan tienen 0. Hoy no se usan: Shannon y Random Forest laboral trabajan con 287.',
     'dataset_fase35.csv, dataset_fase35_33_variables.csv; lugar_trabajo_comprensivo, estres_entorno_laboral', 'No', 'No',
     'No hoy; es un riesgo para la Fase 36 si se usan esas columnas con las 529', 'No', 'No', 'Definir su tratamiento antes de la Fase 36. No regenerar el conjunto ahora.'],
    ['H07', E, 'imc_categoria se probó con «no informado» como categoría: q 0,073. Sin mezclar con faltantes, solo observado: p 0,007 y q 0,038.',
     '34C asociacion_severidad.csv, informe §6; imc_categoria', 'No', 'Sí: una prueba de 41; ninguna otra cambia de lado', 'No: la Fase 35 usa IMC numérico', 'No', 'No',
     'Agregar en 34C un cuadro complementario, sin reemplazar el histórico.'],
    ['H08', M, 'Bajo peso (n = 2) salió sin aviso por la regla de mínimo 5 por grupo; por eso n = 527.',
     'eda/estadistica.py, 34C; imc_categoria', 'Sí', 'No', 'No', 'No', 'No', 'Aclararlo en la misma nota del IMC. No concluir sobre esa categoría.'],
    ['H09', M, 'En 34C, sobrecarga y cantidad valen 0 si no cuida. En sobrecarga rho 0,069 con las 529 y 0,156 entre cuidadoras.',
     '34C asociacion_severidad.csv; sobrecarga_fisica_emocional, cantidad_personas_cuida', 'No', 'Es otra pregunta, no un error de cálculo', 'No: Shannon evalúa sobrecarga en 239', 'No', 'No',
     'Aclararlo en 34C, informando el resultado entre cuidadoras.'],
    ['H10', E, '46 de 65 figuras 34D muestran imputados como «n válido», sin indicarlo; 41 dicen «faltante = 0». Porcentajes aritméticamente correctos.',
     'eda/univariado.py, figuras/eda_univariado/, frecuencias/ de 34C', 'Sí', 'No', 'No', 'No', 'No',
     'Cambiar subtítulos y generar copias nuevas. Con autorización, sin sobrescribir las históricas.'],
    ['H11', E, 'imputados_34B es una cota contada sobre 546 cuando no hay marca: difiere en 9 variables, por 1 a 3 celdas (diabetes 24 frente a 23).',
     'eda/univariado.py, eda_univariado_resumen.csv', 'Sí', 'Solo esa columna', 'No', 'No', 'No', 'Publicar la tabla exacta de esta auditoría como anexo.'],
    ['H12', D, 'El informe 34E dice «Sin imputaciones», pero carga dataset_fase35.csv, con las imputaciones de 34B, salvo IMC y laborales.',
     'informe_eda_multivariado.md §2', 'Sí', 'No', 'No', 'No', 'No', 'Precisar la frase.'],
    ['H13', D, 'Texto y CSV de 34C dicen etapa «descriptiva»; el script aún la trata como control, y volver a ejecutarlo reintroduce el texto antiguo.',
     'eda/variables.py, eda_usuaria.py, informe_eda_usuaria.md', 'Sí', 'No', 'No', 'No', 'No', 'Alinear el script solo cuando se autorice volver a ejecutar 34C.'],
    ['H14', D, 'La figura de 34E dice «38 predictoras»; el texto habla de 35 predictoras y hoy el conjunto inicial es de 33. El código adaptado de 34E no se ha ejecutado completo.',
     'matriz_asociacion.png, informe_eda_multivariado.md, eda/multivariado.py', 'Sí', 'No', 'No', 'No', 'No', 'Agregar nota: 38 exploratorias, 35 históricas, 33 vigentes.'],
    ['H15', D, '34C dice que el IMC entra como categoría con «no informado» y no se imputa; la Fase 35 lo imputa por la media desde el 27-10.',
     'informe_eda_usuaria.md, líneas 772 y 1157', 'Sí', 'No', 'No', 'No', 'No', 'Agregar nota con la decisión del 27-10.'],
    ['H16', D, 'La sección 6.3 dice «cambió por error 1» y su tabla lista 197: 1 celda de cintura y 196 por la regla de pareja.',
     'informe_limpieza_usuaria.md §6.3', 'Sí', 'No', 'No', 'No', 'No', 'Separar la tabla en «error» y «regla del análisis».'],
    ['H17', M, 'Random Forest identificó imputadas con celdas vacías del conjunto sucio: en 10 variables encontró menos. En la sensibilidad, afecta a cantidad (6 de 7).',
     'revision_imputaciones_34B.csv, sensibilidad_imputacion.csv', 'No', 'No', 'No', 'No', 'No: sensibilidad «sin diferencia clara» y efecto de 1 celda', 'Mencionarlo como limitación en el informe de Random Forest.'],
]


def main():
    with (TABLAS / 'matriz_impacto.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(COLUMNAS)
        w.writerows(FILAS)
    datos = {}
    for ruta in sorted(TABLAS.glob('*.csv')):
        if ruta.stem == 'indicadores_auditoria':
            continue
        t = pd.read_csv(ruta, encoding='utf-8-sig')
        datos[ruta.stem] = json.loads(t.to_json(orient='records', force_ascii=False))
    datos['resumen'] = json.loads((TABLAS / 'resumen.json').read_text(encoding='utf-8'))
    (TABLAS / 'tablas.json').write_text(json.dumps(datos, ensure_ascii=False), encoding='utf-8')
    print(len(FILAS), 'hallazgos')


if __name__ == '__main__':
    main()
