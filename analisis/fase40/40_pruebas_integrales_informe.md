# Fase 40 — Pruebas integrales (informe único)

Fecha: 2026-11-06 · Rama `datos-simulados` · Sin commit ni push · Sin cambios de código ni migraciones · Base de desarrollo y análisis históricos intactos.

## Resultados

| Conjunto | Ejecutadas | Aprobadas | Omitidas | Fallidas |
|---|---|---|---|---|
| Django, suite completa | 354 | 353 | 1 (ya existente: `analisis/` no está montado en Docker; verificado aparte) | 0 |
| JavaScript (`pruebas_js`) | 18 | 18 | 0 | 0 |
| Integridad 40B-0 y protección histórica 40B-1 (6.457 artefactos de las Fases 34–39) | 20 | 20 | 0 | 0 |
| **Recorrido integral en Chrome real** (escritorio, móvil 390 px y desconexión) | 30 | 30 | 0 | 0 |

**Entorno del recorrido:** aislado, con base PostgreSQL nueva, secretos aleatorios, cuentas `@ficticio.cl` y puerto 8010. Al terminar se eliminó. Evidencia en `evidencias_privacidad/resultados_navegador_integral.json`.

**Recorrido cubierto:**
- consentimiento: consentimiento nuevo tras el retiro;
- encuesta y sincronización: el cliente cifra IndexedDB y envía lo pendiente;
- **cierre de ronda desde el cliente**: la ronda pasa de 2 a 3;
- MRS y **evolución con 2 rondas**;
- grupo B1: «Grupo 4 — Entre múltiples actividades»;
- orientaciones, con el aviso permanente y la marca **«Versión de prueba, no validada clínicamente»** (`borrador_no_validado`);
- **consulta profesional autorizada**: búsqueda por POST, ficha con evolución y sin la sección del grupo;
- retiro y nueva participación;
- aislamiento entre cuentas;
- dos pestañas;
- «Salir» con y sin conexión;
- dispositivo desactualizado;
- registro rechazado para una cuenta sin consentimiento;
- consola sin errores.

## Problemas detectados

| Gravedad | Problema | Cómo reproducirlo |
|---|---|---|
| — | **No se encontraron errores críticos ni importantes** | — |
| Menor (comportamiento diseñado, a revisar) | Si una ronda se cierra **sin** responder la pareja (MRS complementario) o la actividad física, su grupo B1 queda como «Grupo aún no disponible», aunque la ronda anterior sí tenía grupo. No se infiere, por diseño, pero la participante puede percibir que «perdió» su grupo | 1. Cerrar la ronda 1 con pareja, días de ejercicio y trabajo. 2. Cerrar la ronda 2 respondiendo solo los 11 ítems del MRS. 3. En `/mi-tablero/`, la sección dice «Grupo aún no disponible». *Opción para decidir: mostrar el grupo de la última ronda que lo tenga, indicando de qué ronda es* |
| Menor (de la prueba, no de la plataforma) | El plazo de 15 días entre rondas impide responder de nuevo en la misma prueba. Se simuló moviendo la fecha en la base aislada | — |

## Pendientes (fuera del alcance de hoy)

**Programado para el domingo 8 de noviembre:**
- tablero estadístico profesional (40E);
- correcciones adicionales de seguridad: duración de la sesión y rotación de `SECRET_KEY` (que invalida los borradores locales).

**Esperan una decisión:**
- consentimiento presencial (DC);
- constancia mínima del retiro (migración y conservación legal);
- validación clínica del catálogo 40D (R-1/R-2/R-4 y nota de actividad física).

**Al final de la Fase 40:** commit, mostrando antes el mensaje exacto.
