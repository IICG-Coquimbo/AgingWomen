# Fase 40D — Implementación mínima de orientaciones educativas

**Fecha:** 2026-11-06 · **Rama:** `datos-simulados` · **Estado:** implementada y probada; **sin commit ni push**; en revisión.

Las orientaciones son educativas y personalizadas solo por las respuestas MRS. Los grupos de caracterización no se usan: la evidencia de las Fases 36–39 es exploratoria e insuficiente. La posibilidad de agregarlos en el futuro queda abierta, pero no se activa.

No se modificaron las Fases 34–39 ni los modelos, no hay migraciones y no se cambió de rama.

## 1. Protección: el contenido no validado no llega a participantes reales

- Hay dos variables de entorno nuevas, y las dos están **apagadas por defecto**:
  - `ORIENTACIONES_HABILITADAS`;
  - `ORIENTACIONES_PERMITIR_BORRADOR`.
- La sección se muestra solo si está habilitada **y** se cumple una de estas condiciones:
  - el catálogo tiene estado `aprobado`;
  - se permite expresamente el borrador.
- El catálogo actual tiene estado `borrador_no_validado`. Por eso, en cualquier entorno sin esas dos variables activas, **no se muestra nada**.
- Cuando se muestra el borrador (solo en pruebas sintéticas), aparece un aviso visible: «Versión de prueba: … no está validado clínicamente».

## 2. Cambios

| Archivo | Cambio |
|---|---|
| `analisis/fase40/40D_orientaciones/generar_catalogo_json.py` (nuevo) | Genera el catálogo a partir de `40D-1_catalogo_borrador.md` y `40D-1_fuentes.md`, que siguen siendo la única fuente del contenido. Comprobado: dos ejecuciones dan un archivo idéntico |
| `src/apps/encuestas/orientaciones_catalogo.json` (nuevo, generado) | Versión `catalogo-40D1-borrador-2026-11-06`: aviso, 11 orientaciones y 22 fuentes con enlace y fecha de consulta |
| `src/apps/encuestas/orientaciones.py` (nuevo) | Activación (§1) y selección según las reglas R-1 a R-7. Reutiliza `construir_historial` y la regla única `resultado_mrs`, sin consultas propias |
| `src/templates/encuestas/_orientaciones.html`, `_orientacion.html` (nuevos) | La sección y la tarjeta de cada orientación |
| `src/apps/encuestas/tablero.py`, `mi_tablero.html` | La sección se agrega solo al tablero de la participante, después de los resultados MRS |
| `src/Encuesta_integral/settings.py`, `.env.example` | Las dos variables de entorno, documentadas |
| `src/static/css/tema.css`, `src/static/js/sw.js` | Estilos de la sección; caché v15. `test_40c.py` se actualizó a la versión v15 |
| `src/apps/encuestas/test_orientaciones.py` (nuevo) | 13 pruebas |

## 3. Reglas aplicadas

Son las de la 40D-1, con los valores propuestos ahí. Están como constantes en `orientaciones.py` para poder ajustarlas tras la revisión.

- **R-1:** solo se usa la última ronda cerrada, y solo si su MRS es DEFINITIVO. Si esa ronda no es verificable, no se usa una anterior.
- **R-2:** se destaca un tema si su respuesta tiene intensidad 2 de 4 o más.
- **R-3:** se ordenan de mayor a menor intensidad y se muestran como máximo 3. Las demás quedan en «Otros temas que marcaste».
- **R-4:** si la pregunta 5 (ánimo decaído) tiene intensidad 3 de 4 o más, su orientación (O-05, que incluye la línea \*4141 y el SAMU 131) aparece primero y no se repite más abajo.
- **R-5:** las secciones «¿Cuándo consultar a un profesional de salud?» y «Señales de alerta» nunca van plegadas.
- **R-6:** si no hay ningún tema destacado, se muestra un mensaje neutro y la biblioteca completa.
- **R-7:** cada tema explica por qué aparece: «… marcaste esta molestia con intensidad X de 4».
- **Qué no se usa:** el puntaje total, las dimensiones, la severidad, la comparación entre rondas ni los grupos de caracterización.

## 4. Cumplimiento de los criterios C-1 a C-8

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| C-1 Aviso de no diagnóstico | Texto fijo al inicio de la sección | `test_aviso_permanente…` |
| C-2 «¿Cuándo consultar…?» | Presente en las 11 orientaciones, con fuente | `test_catalogo_cumple_c1_a_c8` |
| C-3 Sin diagnóstico ni fármacos | Lista de expresiones vetadas; la advertencia «No lo suspendas por tu cuenta» está presente | Ídem |
| C-4 Señales de alerta | En las 9 orientaciones con respaldo; en sueño y cansancio, el texto «No se identificaron…» | Ídem |
| C-5 Grupos | No intervienen en la selección | Ídem y `test_usa_la_ultima_ronda…` |
| C-6 Fuentes | Cada tarjeta muestra sus fuentes, con enlace y fecha de consulta | `test_fuentes_visibles…` |
| C-7 Lenguaje | Trato de tú; sin palabras alarmistas ni categorías de severidad | Vetadas en el catálogo y en la página |
| C-8 Sin confirmaciones | La sección no tiene formulario, casillas ni diálogos | `test_aviso_permanente…` |

## 5. Pruebas ejecutadas (2026-11-06)

| Suite | Resultado |
|---|---|
| `apps.encuestas.test_orientaciones` (40D) | **13/13 OK** |
| Django completo, en orden normal e inverso | **317/317 OK** en ambos |
| `makemigrations --check` | Sin cambios |
| Node (`test_encuesta_sync.mjs`) | **12/12 OK** |
| 40B-0 | **15/15 OK** |
| 40B-1: integridad de las Fases 34–39 | **5/5 OK**; 6.457 artefactos con la misma huella |

Las pruebas de la 40D cubren:
- que la sección esté apagada por defecto;
- que el borrador no se muestre sin permiso expreso;
- el aviso permanente;
- las reglas R-1 a R-4 y R-6;
- el determinismo;
- la ausencia de comparación entre rondas y de severidad;
- que mostrar la página no escriba en la base;
- la integridad del catálogo;
- las fuentes visibles.

**No ejecutado:** la prueba en navegador. La presentación quedó verificada solo con el cliente de pruebas de Django.

## 6. Pendientes

1. **Revisión clínica del catálogo.** Son los 11 puntos de `40D-1_informe.md`, §6. Al aprobarlo, hay que cambiar `estado` a `aprobado` y registrar quién aprobó y cuándo (campo `aprobacion`). Mientras tanto, la sección no puede activarse con participantes reales.
2. **Decisiones pendientes de las reglas:**
   - **R-1:** ronda de referencia;
   - **R-2:** umbral 2 para destacar un tema;
   - **R-4:** umbral 3 para el mensaje de apoyo, su texto y la marca para el profesional (DR-6).
3. **Trazabilidad persistente (R-8):** no hay registro en la base de qué se mostró, porque requeriría una migración. Hoy la versión del catálogo queda solo en la página (`data-version-catalogo`). Hay que decidir si se agrega.
4. **Prueba en navegador** (escritorio y móvil), con datos sintéticos.
5. **Ficha profesional:** no muestra las orientaciones. Decidir si debe mostrarlas.
6. Todo sigue local hasta cerrar la Fase 40, como se pidió.

## 7. Activación en el piloto local (2026-11-06)

- **Configuración activa en este computador:** `.env.desarrollo`, archivo privado e ignorado por git, con `ORIENTACIONES_HABILITADAS=1` y `ORIENTACIONES_PERMITIR_BORRADOR=1`. `DEBUG=1` ya venía de `docker-compose.yml`. Se recreó el contenedor `web`.
- **Comprobación:** `habilitadas()` devuelve `True`. El catálogo sigue en estado `borrador_no_validado`.
- **Valores por defecto del proyecto:** no cambiaron. `settings.py` y `.env.example` siguen en 0.
- **En el computador de la compañera:** debe agregar esas dos líneas a su propio `.env.desarrollo` y ejecutar `docker compose up -d web`.
- **Protección nueva:** el modo borrador exige además `DEBUG=True` (`orientaciones.habilitadas()`). Con `DEBUG=False`, que es lo que corresponde a producción, el borrador no se muestra aunque las variables queden activadas.
- **Etiqueta:** el texto visible es exactamente «Versión de prueba, no validada clínicamente.».

**Pruebas:**
- **40D:** 16/16 OK. Se agregaron tres pruebas:
  - borrador con `DEBUG=False`;
  - permitir el borrador sin habilitar las orientaciones;
  - valores por defecto del proyecto en falso.
- **Django completo:** 320/320 OK.
- **Navegador:** Chrome sin interfaz, en escritorio (1280 px) y móvil (390 px), **17/17 OK**. Se usó un entorno aislado con la misma imagen, el mismo código, la misma configuración del piloto y solo cuentas sintéticas. La base de desarrollo no se tocó, y el entorno se eliminó al terminar. Se comprobó:
  - la participante sintética con su última ronda cerrada y verificable ve el apoyo (O-05) y los temas O-01, O-02 y O-03;
  - el aviso, la etiqueta de versión de prueba, «¿Cuándo consultar…?» y las señales de alerta están visibles;
  - no hay controles de confirmación;
  - no hay desplazamiento horizontal;
  - la consola no muestra errores;
  - los casos «sin temas destacados» y «sin rondas» se ven bien.

  Evidencia en `evidencias_40D/`.
