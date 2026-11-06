"""
Fase 37C: registra las Listas A y B y el conjunto priorizado. Lee las listas de sus archivos originales: no las reconstruye.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/candidatos_37c.py
"""
import nucleo_37c as N
import pandas as pd

COLS = ['espacio', 'metodo', 'con_imc', 'componentes', 'algoritmo', 'k', 'silueta', 'silueta_negativos', 'ari_completo_media', 'ari_entre_media', 'ari_entre_p05', 'ari_entre_min', 'ari_fuera_media', 'tam_min', 'tam_max', 'equilibrio', 'fraccion_eje1',
        'senal_eje1', 'senal_repeticiones_inestables', 'senal_grupos_pequenos', 'sens_Codificación', 'sens_Población', 'sens_Variables', 'sens_Ponderación', 'acuerdo_prototipo_ari']


def main():
    N.huella_sello()
    S = N.BASE / 'candidatos'
    t = N.tabla_37b()
    a, b, p = N.lista_a(), N.lista_b(), N.priorizadas()
    if not set(b) <= set(a):
        raise SystemExit('Una configuración de la Lista B no está en la Lista A.')
    ta = t.loc[a, COLS].reset_index()
    ta.insert(1, 'en_lista_b', ta['config'].isin(b))
    ta.insert(2, 'origen', 'Regla previa de la Fase 37B (sección 11 de su protocolo)')
    N.a_csv(ta, S / 'lista_A_completa.csv')
    tb = t.loc[b, COLS].reset_index()
    tb.insert(1, 'caracter', 'Exploratoria: definida después de examinar los resultados de la Fase 37B')
    tb.insert(2, 'fuente', 'fase37/37B_clustering/informes/17_preparacion_37C.docx, segunda tabla')
    N.a_csv(tb, S / 'lista_B_exploratoria.csv')
    filas = [{'config': c, 'motivo': m, 'en_lista_a': c in a, 'en_lista_b': c in b, 'en_vista_a': c in N.vista_a(), **N.info_config(c)} for c, m in p.items()]
    N.a_csv(pd.DataFrame(filas), S / 'conjunto_priorizado.csv')
    N.a_csv(pd.DataFrame({'config': sorted(set(a) | set(p))}), S / 'conjunto_estabilidad.csv')
    res = {'lista_A': len(a), 'lista_A_eje1': int(t.loc[a, 'senal_eje1'].sum()), 'lista_A_inestables': int(t.loc[a, 'senal_repeticiones_inestables'].sum()), 'lista_B': len(b), 'lista_B_en_A': sum(c in a for c in b),
           'vista_A': len(N.vista_a()), 'priorizadas': len(p), 'evaluadas_en_estabilidad': len(set(a) | set(p)), 'fuera_de_A_en_priorizadas': sum(c not in a for c in p)}
    N.a_json(res, S / 'resumen_listas.json')
    print(res)


if __name__ == '__main__':
    main()
