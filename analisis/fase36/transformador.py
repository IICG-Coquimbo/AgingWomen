"""
Fase 36B: transformador sin estado. Aplica parámetros guardados en JSON y nunca los recalcula.

`calibrar` se usa una sola vez, con los datos de referencia. `Transformador` solo lee el resultado, de modo que transformar
a una participante nueva no puede cambiar medias, desviaciones ni proporciones. No depende de scikit-learn ni de pickle.

Entrada: una tabla con las respuestas tal como las guarda el conjunto limpio, más las preguntas madre (campos de contexto).
Ninguna variable del MRS, de los módulos ni de auditoría se lee aquí: solo se usan las columnas listadas en el esquema.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ARCHIVOS = {'esquema': 'esquema_variables.json', 'orden': 'orden_columnas.json', 'codificadores': 'codificadores.json',
            'escaladores': 'escaladores.json', 'desconocidos': 'valores_desconocidos.json'}
VACIOS = {'', 'nan', 'none', '<na>'}


class ErrorValor(ValueError):
    """Una respuesta no admitida por el instrumento: no se asigna perfil."""


def _texto(valor):
    if valor is None or (isinstance(valor, float) and math.isnan(valor)) or valor is pd.NA:
        return ''
    if isinstance(valor, (bool, np.bool_)):
        return 'True' if valor else 'False'
    if isinstance(valor, (int, np.integer)):
        return str(int(valor))
    if isinstance(valor, (float, np.floating)):
        return str(int(valor)) if float(valor).is_integer() else repr(float(valor))
    t = str(valor).strip()
    if t.lower() in VACIOS:
        return ''
    if t.endswith('.0') and t[:-2].lstrip('-').isdigit():
        return t[:-2]
    return t


def leer_niveles(datos, definiciones):
    """
    Valida y normaliza. Devuelve (niveles, avisos): `niveles` tiene un valor por celda (texto o número) y NaN si la respuesta
    falta y no la cubre una regla condicional; `avisos` lista lo que no fue una respuesta directa, sin alterar el valor original.
    """
    niveles = pd.DataFrame(index=datos.index)
    avisos = []
    for d in definiciones:
        v = d['variable']
        if v not in datos.columns:
            raise ErrorValor(f'Falta la columna {v} en la entrada.')
        crudo = datos[v].map(_texto)
        if d['tipo'] == 'cuantitativa':
            salida = pd.Series(np.nan, index=datos.index, dtype=float)
            for i, t in crudo.items():
                if t == '':
                    continue
                try:
                    x = float(t)
                except ValueError as e:
                    raise ErrorValor(f'{v}: valor no numérico {t!r}') from e
                bajo, alto = d['limites']
                if not bajo <= x <= alto:
                    raise ErrorValor(f'{v}: valor imposible {x}')
                salida[i] = x
            niveles[v] = salida
            continue
        admitidos = set(d['niveles'])
        madre = d.get('madre')
        salida = pd.Series(np.nan, index=datos.index, dtype=object)
        for i, t in crudo.items():
            if madre:
                if madre['variable'] not in datos.columns:
                    raise ErrorValor(f'Falta la pregunta madre {madre["variable"]} de {v}.')
                m = _texto(datos.at[i, madre['variable']])
                if t == '' and m == madre['no']:
                    t = madre['estructural']
                    avisos.append((i, v, 'estructural', f'{madre["variable"]} = {m}'))
                elif t == '' and m == '':
                    # Igual que la limpieza: la madre ausente toma su moda (NO) y la pregunta no se muestra.
                    t = madre['estructural']
                    avisos.append((i, v, 'madre_ausente', f'{madre["variable"]} vacía: se aplica el nivel estructural'))
                elif t not in ('', madre['estructural']) and m == madre['no']:
                    raise ErrorValor(f'{v}: tiene respuesta {t!r} con {madre["variable"]} = NO')
            if t == '':
                continue
            if t not in admitidos:
                raise ErrorValor(f'{v}: nivel {t!r} no admitido por el instrumento')
            if t == '1' and d.get('nunca_unificado'):
                avisos.append((i, v, 'nunca_unificado', 'Respuesta original «Nunca» tratada como frecuencia efectiva cero'))
            salida[i] = t
        niveles[v] = salida
    return niveles, avisos


def _estandarizar(x, media, de):
    return (np.asarray(x, dtype=float) - media) / de


def _guardar_json(objeto, ruta):
    ruta.write_text(json.dumps(objeto, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


def calibrar(datos, definiciones, ruta, modo_ordinal='consecutivo', roles=None, grupos=None, filas_ajuste=None, excluir_de_congelado=None):
    """
    Calcula una sola vez los parámetros de un escenario.

    ruta: 'pca' o 'famd'. roles: en FAMD, variable -> 'cuantitativa' o 'categorica'. grupos: en FAMD, variable -> {grupo: [niveles]},
    fijados de antemano. filas_ajuste: máscara de las filas de referencia; por defecto, todas.
    excluir_de_congelado: tabla booleana (variable -> celda imputada) para que el valor congelado salga solo de respuestas reales.
    """
    if ruta not in ('pca', 'famd') or modo_ordinal not in ('consecutivo', 'ridit'):
        raise ValueError('Ruta o modo ordinal no reconocidos.')
    niveles, _ = leer_niveles(datos, definiciones)
    filas = pd.Series(True, index=datos.index) if filas_ajuste is None else pd.Series(filas_ajuste, index=datos.index).astype(bool)
    ref = niveles[filas]
    if ref.empty:
        raise ValueError('Sin filas de referencia.')
    codificadores, escaladores, orden, congelados, esquema = {}, {}, [], {}, []
    for d in definiciones:
        v, tipo = d['variable'], d['tipo']
        rol = None
        if ruta == 'famd':
            rol = (roles or {}).get(v) or d.get('rol_famd')
            if rol not in ('cuantitativa', 'categorica'):
                raise ValueError(f'{v}: sin rol para FAMD')
        serie = ref[v]
        presentes = serie.dropna()
        if presentes.empty:
            raise ValueError(f'{v}: sin datos en la referencia')
        cod = {'tipo': tipo}
        categorica = (ruta == 'famd' and rol == 'categorica') or (ruta == 'pca' and tipo == 'nominal')
        if tipo != 'cuantitativa':
            cod['mapa'] = {k: x['codigo'] for k, x in d['niveles'].items()}
        if categorica:
            mapa_grupos = (grupos or {}).get(v) or d.get('grupos_famd') if ruta == 'famd' else {k: [k] for k in d['niveles']}
            if mapa_grupos is None:
                mapa_grupos = {k: [k] for k in d['niveles']}
            cubiertos = [n for g in mapa_grupos.values() for n in g]
            if set(cubiertos) != set(d['niveles']) or len(cubiertos) != len(set(cubiertos)):
                raise ValueError(f'{v}: los grupos no cubren exactamente los niveles del instrumento')
            nivel_a_grupo = {n: g for g, ns in mapa_grupos.items() for n in ns}
            frec = presentes.map(nivel_a_grupo).value_counts()
            n = len(presentes)
            props = {g: int(frec.get(g, 0)) / n for g in mapa_grupos}
            cod.update({'modo': 'indicadoras', 'grupos': mapa_grupos, 'proporciones': props})
            if ruta == 'famd':
                vacios = [g for g, p in props.items() if p == 0]
                if vacios:
                    raise ValueError(f'{v}: categorías con frecuencia cero en FAMD ({vacios}); deben unirse a un grupo con observaciones')
                for g, p in props.items():
                    col = f'{v}__{g.replace(" ", "")}'
                    escaladores[col] = {'variable': v, 'clase': 'indicadora_famd', 'grupo': g, 'p': p, 'divisor': math.sqrt(p)}
                    orden.append(col)
            else:
                divisor = math.sqrt(sum(p * (1 - p) for p in props.values()))
                if divisor == 0:
                    raise ValueError(f'{v}: variable constante en la referencia')
                for g, p in props.items():
                    col = f'{v}__{g.replace(" ", "")}'
                    escaladores[col] = {'variable': v, 'clase': 'indicadora_pca', 'grupo': g, 'p': p, 'divisor': divisor}
                    orden.append(col)
        else:
            if tipo == 'cuantitativa':
                numeros = presentes.astype(float).to_numpy()
                cod['modo'] = 'valor'
            else:
                mapa = cod['mapa']
                if tipo == 'ordinal' and modo_ordinal == 'ridit':
                    # El ridit se calcula sobre la escala del instrumento, incluidos los niveles sin observaciones.
                    frecuencia = presentes.map(mapa).value_counts()
                    codigos = sorted(set(mapa.values()))
                    acumulado, ridit = 0.0, {}
                    for c in codigos:
                        f = int(frecuencia.get(c, 0)) / len(presentes)
                        ridit[c] = acumulado + f / 2
                        acumulado += f
                    cod.update({'modo': 'ridit', 'ridit': {k: ridit[c] for k, c in mapa.items()}})
                    numeros = presentes.map(cod['ridit']).astype(float).to_numpy()
                else:
                    cod['modo'] = 'consecutivo'
                    numeros = presentes.map(mapa).astype(float).to_numpy()
            de = float(np.std(numeros))
            if de == 0:
                raise ValueError(f'{v}: variable constante en la referencia (DE = 0); no se elimina en silencio')
            escaladores[v] = {'variable': v, 'clase': 'z', 'media': float(np.mean(numeros)), 'de': de, 'n_referencia': int(len(numeros)),
                              'minimo_referencia': float(numeros.min()), 'maximo_referencia': float(numeros.max())}
            orden.append(v)
        codificadores[v] = cod
        # Valor congelado para una respuesta ausente. La misma regla de la limpieza: IMC por la media; moda o mediana inferior en los demás.
        reales = presentes
        if excluir_de_congelado is not None and v in excluir_de_congelado:
            reales = presentes[~excluir_de_congelado.loc[presentes.index, v].astype(bool)]
        if tipo == 'cuantitativa':
            congelado = float(np.mean(numeros)) if d.get('ausente_es_media') else float(np.median(reales.astype(float)))
        elif tipo == 'ordinal':
            base = reales
            if d.get('madre'):
                base = reales[reales != d['madre']['estructural']]
            congelado = str(sorted(base, key=lambda n: d['niveles'][n]['codigo'])[(len(base) - 1) // 2])
        else:
            congelado = reales.value_counts().sort_index().idxmax()
        congelados[v] = congelado
        esquema.append({k: d[k] for k in ('variable', 'tipo', 'seccion') if k in d} | {
            'rol': rol or ('categorica' if categorica else 'cuantitativa'), 'madre': d.get('madre'), 'limites': d.get('limites'),
            'nunca_unificado': bool(d.get('nunca_unificado')), 'ausente_es_media': bool(d.get('ausente_es_media')),
            'niveles': d.get('niveles')})
    return {'esquema': {'ruta': ruta, 'modo_ordinal': modo_ordinal, 'filas_referencia': int(filas.sum()),
                        'reescalar_prohibido': 'Las columnas ya llevan su peso. No aplicar otra estandarización antes de PCA.',
                        'variables': esquema},
            'orden': orden, 'codificadores': codificadores, 'escaladores': escaladores,
            'desconocidos': {'reglas': REGLAS_DESCONOCIDOS, 'valor_congelado': congelados}}


REGLAS_DESCONOCIDOS = {
    'nivel_no_admitido': 'Error: no se asigna perfil.',
    'nivel_valido_no_observado': 'Se transforma normalmente con los parámetros congelados, aunque quede fuera del rango de referencia.',
    'pregunta_no_mostrada': 'Nivel estructural de cero cuando la madre vale NO o falta.',
    'imc_ausente': 'Media congelada de las observadas: z = 0, con marca.',
    'otra_ausente': 'Valor congelado de la variable, con marca y aviso. El límite de respuestas ausentes queda pendiente (D-09).',
}


class Transformador:
    """Aplica un escenario guardado. No tiene método de ajuste."""

    def __init__(self, parametros):
        self.p = parametros
        self.definiciones = parametros['esquema']['variables']

    @classmethod
    def cargar(cls, carpeta):
        carpeta = Path(carpeta)
        return cls({k: json.loads((carpeta / a).read_text(encoding='utf-8')) for k, a in ARCHIVOS.items()})

    def guardar(self, carpeta):
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        for k, a in ARCHIVOS.items():
            _guardar_json(self.p[k], carpeta / a)

    def transformar(self, datos):
        """Devuelve (matriz, avisos). La matriz tiene exactamente las columnas y el orden guardados."""
        datos = datos.copy()
        niveles, avisos = leer_niveles(datos, self.definiciones)
        congelados = self.p['desconocidos']['valor_congelado']
        for d in self.definiciones:
            v = d['variable']
            faltan = niveles[v].isna()
            for i in niveles.index[faltan]:
                avisos.append((i, v, 'imc_ausente' if d.get('ausente_es_media') else 'ausente', 'Se usa el valor congelado'))
            if faltan.any():
                niveles.loc[faltan, v] = congelados[v]
        salida = {}
        for col in self.p['orden']:
            e = self.p['escaladores'][col]
            v = e['variable']
            cod = self.p['codificadores'][v]
            if e['clase'] == 'z':
                if cod['modo'] == 'valor':
                    x = niveles[v].astype(float)
                else:
                    x = niveles[v].map(cod['ridit'] if cod['modo'] == 'ridit' else cod['mapa']).astype(float)
                salida[col] = _estandarizar(x, e['media'], e['de'])
                fuera = (x < e['minimo_referencia']) | (x > e['maximo_referencia'])
                for i in x.index[fuera]:
                    avisos.append((i, v, 'fuera_rango_referencia', f'{x[i]} fuera de [{e["minimo_referencia"]}, {e["maximo_referencia"]}]'))
            else:
                a_grupo = {n: g for g, ns in cod['grupos'].items() for n in ns}
                indicadora = (niveles[v].map(a_grupo) == e['grupo']).astype(float).to_numpy()
                salida[col] = (indicadora - e['p']) / e['divisor']
        matriz = pd.DataFrame(salida, index=datos.index)[self.p['orden']]
        if not np.isfinite(matriz.to_numpy()).all():
            raise ErrorValor('La matriz transformada contiene valores no finitos.')
        return matriz, pd.DataFrame(avisos, columns=['fila', 'variable', 'marca', 'detalle'])


def pesos_por_bloque(matriz, escaladores, bloques):
    """
    Multiplicadores de columna para que cada bloque aporte la misma inercia total, conservando la inercia global.
    Es solo preparación de S-BLOQUE: no se aplica a las matrices principales ni a ningún agrupamiento.
    """
    inercia = {}
    for col in matriz.columns:
        b = bloques[escaladores[col]['variable']]
        inercia[b] = inercia.get(b, 0.0) + float(np.var(matriz[col].to_numpy()))
    total = sum(inercia.values())
    objetivo = total / len(inercia)
    return {'inercia_por_bloque': inercia, 'inercia_total': total, 'objetivo_por_bloque': objetivo,
            'multiplicador_por_bloque': {b: math.sqrt(objetivo / x) for b, x in inercia.items()},
            'multiplicador_por_columna': {col: math.sqrt(objetivo / inercia[bloques[escaladores[col]['variable']]]) for col in matriz.columns}}
