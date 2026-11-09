# AgingWomen — Informe final de la plataforma

Fecha: 2026-11-09 · Rama `datos-simulados` · HEAD `573d3a3` · Todo el trabajo queda **sin commit ni push**.

**Conclusión: lista con restricciones** (detalle en el punto 10). Sirve para la revisión académica en un entorno controlado con datos sintéticos. No está lista para recibir a participantes reales.

Todas las pruebas se ejecutaron en copias aisladas, con bases temporales y datos sintéticos. No se usaron las bases de desarrollo, no se enviaron correos reales y no se abrieron los cuatro archivos protegidos.

---

## 1. Funcionalidades terminadas

| Área | Estado |
|---|---|
| Registro con código, consentimiento informado e ingreso por RUT | Terminado y probado |
| Encuesta por rondas: guardado, cierre, sincronización y funcionamiento sin conexión | Terminado y probado |
| Protección frente a páginas antiguas, «Atrás» y varias pestañas (Etapa 5B-3) | Conservada y probada |
| Conservación de respuestas durante un guardado lento, una recarga o un corte de conexión | Conservada y probada |
| Resultado MRS y su evolución | Terminado y probado |
| Grupo B1 visible para la participante, con avisos exploratorios y motivo cuando no está disponible | Terminado y probado |
| Tablero de la participante | Terminado y probado |
| Ficha y estadísticas para profesionales, agregadas por grupo con mínimo de publicación | Terminado y probado |
| Retiro digital y presencial con comprobante | Terminado y probado |
| Límites de intentos, activación por enlace y protección de caché | **Nuevo**, terminado y probado |
| Uso táctil de la encuesta (primer toque después de la fecha) | **Corregido** y probado en emulación móvil |
| Orientaciones educativas | Funcionan, pero **apagadas por defecto**: su catálogo es un borrador no validado (punto 6) |

---

## 2. Archivos modificados y justificación

Cambios posteriores a la Etapa 5B-3. Los de la 5B-3 constan en `INFORME_ETAPA_5B3.md` y se conservaron.

**Seguridad de acceso**

| Archivo | Justificación |
|---|---|
| `src/apps/usuarios/limite_ingreso.py` (nuevo) | Contadores de intentos de ingreso, recuperación y registro |
| `src/apps/usuarios/vistas_clave.py` (nuevo) | Recuperación con límite; desbloquea al completarla |
| `src/apps/usuarios/sin_cache.py` (nuevo) | Impide que el navegador guarde páginas de una sesión iniciada |
| `src/apps/usuarios/test_seguridad_acceso.py` (nuevo) | 21 pruebas de lo anterior |
| `src/Encuesta_integral/settings.py` | Activa el middleware, la vigencia del enlace (24 h) y los límites |
| `src/apps/usuarios/forms.py` | Aplica el límite al iniciar sesión |
| `src/apps/usuarios/urls.py` | Usa las nuevas vistas de recuperación |
| `src/apps/usuarios/managers.py` | Deja de generar una contraseña para comunicarla |
| `src/apps/usuarios/views.py`, `administracion.py`, `admin.py` | Envían un enlace de activación en vez de una contraseña; límite de registro |
| `src/apps/usuarios/management/commands/crear_profesional.py` | Ya no muestra contraseña e indica «Olvidé mi contraseña» |
| `src/templates/admin/usuarios/crear_profesional.html` | Texto acorde a la activación por enlace |

**B1 (sin cambios en su regla ni en su cálculo)**

| Archivo | Justificación |
|---|---|
| `src/apps/encuestas/contexto_participante.py` | Explica el motivo de ausencia: `sin_ronda`, `no_verificable`, `faltan_datos` |
| `src/templates/encuestas/_mi_grupo.html` | Muestra ese motivo |
| `src/apps/encuestas/orientaciones.py`, `tablero.py` | Comentarios que aún decían que B1 no se mostraba |
| `src/apps/encuestas/test_contexto_participante.py` | 4 pruebas de motivos; una prueba renombrada para reflejar lo que comprueba |

**Encuesta en dispositivos táctiles**

| Archivo | Justificación |
|---|---|
| `src/static/js/encuesta.js` | El primer toque tras la fecha se perdía; ahora se detecta |
| `src/static/js/sw.js` | Versión 22, para que los navegadores reciban el cambio |
| `src/apps/rondas/test_40c.py` | Espera la versión 22 |
| `src/apps/encuestas/pruebas_js/test_encuesta_sync.mjs` | Prueba táctil nueva |

**Documentos con nota de actualización sobre B1**

`analisis/fase40/40D_orientaciones/00_criterios_obligatorios_40D.md`, `40D-1_informe.md`, `40D-1_reglas_personalizacion.md`, `40D-G_informe.md` y `analisis/fase40/40A_auditoria/01_revision_correctiva_40A.md`.

`informe_fase40A.md` no se editó porque otro documento cita su huella. La nota de la Fase 39R tampoco se tocó, porque 39R no debía modificarse. El informe histórico y esa nota conservan su redacción original; la aclaración consta en la revisión correctiva de la 40A.

---

## 3. Correcciones de seguridad implementadas

**A. Inicio de sesión**

- 5 intentos fallidos por RUT y 30 por conexión, en una ventana de 15 minutos.
- Recuperación de contraseña: 10 solicitudes por conexión y 3 por correo. Registro: 10 por conexión.
- El bloqueo termina solo y también se levanta al recuperar la contraseña, de modo que ninguna cuenta queda bloqueada de forma permanente.
- El mensaje de bloqueo es idéntico exista o no la cuenta.

**B. Contraseñas temporales**

- Ninguna contraseña viaja ya por correo. La cuenta profesional recibe un enlace de un solo uso que vence a las 24 horas.
- Un enlace vencido se reemplaza con «Olvidé mi contraseña».
- Se comprobó con cuentas de prueba y un buzón en memoria.

**C. Caché y sesiones**

- Todas las páginas y respuestas de una sesión iniciada llevan `no-store`, incluidos tablero, fichas, MRS, estadísticas y API.
- Tras «Salir», «Atrás» lleva al ingreso y no muestra datos. Chrome confirmó que no restauró la página desde su caché.
- La encuesta sin conexión sigue funcionando, porque usa su propio almacenamiento cifrado.
- Tras el retiro, el almacenamiento local queda vacío.

**D. Datos almacenados**

| Dato | Protección actual |
|---|---|
| RUT | Solo huella HMAC-SHA256; no se guarda el RUT en claro |
| Contraseñas | Hash de Django |
| Respuestas pendientes en el navegador | IndexedDB cifrado con AES-GCM; se borra al salir o al retirarse |
| Respuestas de salud en la base de datos | **Sin cifrado por campo** |
| Volcados de base de datos y respaldos | **Sin cifrar** y en el mismo disco |

No se implementó cifrado por campo, porque requiere migrar datos. La dependencia `django-fernet-encrypted-fields` figura en `requirements.txt`, pero no se usa. **Antes de aplicarlo hay que autorizar y resolver:**

1. Qué campos se cifran.
2. Dónde se genera y custodia la clave, fuera del repositorio, y cómo se rota. Perder la clave significa perder los datos.
3. Una migración de esquema y de datos con respaldo verificado previo.
4. Reescribir tablero y estadísticas para calcular fuera de SQL, porque un campo cifrado no se puede filtrar ni promediar en la base.
5. Cifrar los volcados y mover los respaldos a otro medio.

El cifrado del disco o del volumen del servidor es una alternativa que no exige migrar datos, aunque protege solo frente al robo del soporte físico.

---

## 4. Resultados de las pruebas finales

Ejecutadas sobre una copia comprobada como idéntica a `src`, salvo dos archivos auxiliares de prueba que existen solo en la copia.

| Prueba | Resultado |
|---|---|
| Django, suite completa | **435 ejecutadas: 434 correctas, 1 omitida, 0 fallos** (427 del proyecto y 8 auxiliares de B1) |
| `manage.py check` | Sin problemas |
| `makemigrations --check` | Sin cambios: **no se requiere migración** |
| JavaScript | **36/36**, en 3 corridas completas consecutivas |
| Prueba P6, la que fue inestable | **12/12** corridas |
| 40B-0, alternativa segura | 15/15 |
| 40B-1, alternativa segura | 5/5; 6.455 artefactos verificados por huella, 7 solo por existencia y 3 excepciones conocidas |
| Chrome real | Todos los escenarios finales sin error |

La prueba omitida (`test_mapa_identico_a_la_definicion_documentada`) compara con un documento de `analisis/`, carpeta que no existe dentro del contenedor. **No se ejecutó.** Las pruebas originales 40B-0 y 40B-1 tampoco se ejecutaron, porque abren un archivo protegido.

`manage.py check --deploy` da 5 avisos en el entorno de prueba, que corre con `DEBUG=1`. Las cookies seguras se activan solas en producción; HTTPS y HSTS dependen de la configuración del servidor (punto 8).

**Escenarios en Chrome**

| Tema | Escenarios | Resultado |
|---|---|---|
| Registro, autenticación | Registro, código, consentimiento, bloqueo, recuperación, activación profesional, enlace reutilizado rechazado | Correcto |
| Permisos | Anónima, participante, profesional y administración en cada ruta | Correcto: cada perfil solo accede a lo suyo |
| Encuesta | Flujo completo, opcionales vacías, volver sin guardar, guardar y recargar, sesión vencida | Correcto |
| Sin conexión | Responder sin conexión y sincronizar | Correcto |
| «Atrás» y pestañas | Página antigua, dos pestañas, decisión explícita de reemplazar | Correcto: no se pierden respuestas sin aviso |
| Guardado en curso | Responder, recargar o cortar la conexión durante el guardado | Correcto |
| Fecha | Primer clic o toque tras la fecha | Correcto |
| Salir y «Atrás» | Participante y profesional | Correcto: vuelve al ingreso, sin datos |
| Vista profesional | 4 grupos: 1 publicado, 3 no publicados por el mínimo, con aviso | Correcto |
| Móvil | **Emulación** a 390 px: sin desborde, con toque real emulado | Correcto, pero **no se probó en un teléfono físico** |

---

## 5. Confirmación del funcionamiento de MRS y B1

**MRS.** Se calcula al cerrar la ronda y se muestra en el tablero. Los registros históricos no verificables se identifican como tales, sin cambiar su valor.

**B1.**

- El algoritmo no se modificó.
- Aparece cuando se cumplen sus condiciones, con su aviso de carácter exploratorio y no diagnóstico.
- Cuando no está disponible, explica el motivo. Se comprobaron en Chrome los casos sin ronda cerrada y con datos faltantes; `no_verificable` está cubierto por las pruebas de Django.
- No aparece en la ficha individual del profesional.
- Las estadísticas agregadas por grupo se mantienen, con su aviso.
- No interviene en la selección de orientaciones; una prueba automática lo comprueba.

Los resultados estadísticos de 38R y 39R no se recalcularon.

---

## 6. Estado de las orientaciones educativas

- **Apagadas por defecto.** Con esa configuración no se muestra ninguna tarjeta y el grupo y su aviso siguen visibles (comprobado en Chrome).
- Activadas en un entorno aislado funcionan: se mostraron 22 tarjetas con el aviso de borrador, junto con el grupo y su aviso.
- **El catálogo es un borrador sin validación clínica.** No debe activarse con participantes reales hasta validarlo.

---

## 7. Resultado de las pruebas de retiro de datos

| Comprobación | Retiro digital | Retiro presencial |
|---|---|---|
| Entrega comprobante | Sí | Sí |
| La ficha deja de existir | Sí | Sí |
| Una clave incorrecta no borra nada | — | Sí |
| Un segundo intento indica que no hay datos | — | Sí |
| Otra pestaña abierta se cierra | Sí | — |
| Un envío antiguo posterior es rechazado (403) | Sí | — |
| «Atrás» no restaura datos | Sí | — |
| IndexedDB queda vacío | Sí | — |

---

## 8. Riesgos o limitaciones que permanecen

**Impiden el uso con participantes reales**

- Falta la validación clínica del catálogo de orientaciones y la validación ético-jurídica.
- Hay que rotar los secretos antes de cualquier despliegue.
- **B1 proviene de datos sintéticos, con evidencia débil** y sin asociaciones robustas en 38R y 39R. Está visible por decisión expresa para la revisión académica. Antes de mostrarlo a mujeres reales debe decidirse si se mantiene.
- HTTPS y HSTS no están configurados, y el cifrado por campo sigue pendiente (punto 3 D).

**Datos**

- **DR-1 sigue sin resolver:** los informes 40S-1 y 40B-2 registran indicios de datos reales en la base de desarrollo. Conviene hacer la demostración en una base limpia.
- Las respuestas ya vaciadas por el defecto de página antigua, antes de la corrección, no se pueden recuperar. No se confirmó si la ficha 14 se vio afectada.
- Hay dos volcados de base de datos sin cifrar en la carpeta de respaldos, y todos los respaldos están en el mismo disco.

**Seguridad residual**

- Los contadores usan la caché local de cada proceso: con varios procesos se necesita una caché compartida.
- Detrás de un proxy hay que configurar `LIMITE_IP_CABECERA`; si no, todas las conexiones cuentan como una sola.
- Un tercero que conozca un RUT puede bloquearlo temporalmente (hasta 15 minutos o hasta recuperar la contraseña).
- Las cuentas profesionales que ya recibieron una contraseña temporal no se pueden identificar ni obligar a cambiarla sin una migración. Conviene pedirles que la cambien.

**Pruebas**

- El móvil solo se probó en emulación.
- Las páginas antiguas que no llevan versión no se comprobaron.
- Las evidencias de Chrome quedan en una carpeta temporal y no forman parte del proyecto ni del respaldo.
- La 40D-H no tiene informe propio; consta en notas.

---

## 9. Estado de los respaldos y archivos pendientes de Git

**Respaldos** (`C:\Users\scarl\Respaldos_AgingWomen\`, privados y sin cifrar)

| Carpeta | Contenido | Verificación |
|---|---|---|
| `2026-11-09_etapa5B1` | 2.034 archivos | Manifiesto correcto; no se sobrescribió |
| `2026-11-09_final_incremental/01_correcciones_5B3` | 10 archivos | Manifiesto SHA-256 |
| `2026-11-09_final_incremental/02_finalizacion` | 29 archivos, incluido este informe | Manifiesto SHA-256; cada copia comparada con su original |

Los respaldos incrementales no incluyen archivos `.env`, secretos, datos reales ni los cuatro archivos protegidos.

**Git**

- Rama `datos-simulados`, HEAD `573d3a3`, sin stash y sin nada en el índice.
- **105 entradas pendientes**: 41 archivos modificados y 64 entradas sin seguimiento.
- Las carpetas **38R y 39R siguen pendientes** de incorporación controlada, junto con todo lo posterior a `573d3a3`.
- No se hicieron commits, pushes ni operaciones destructivas.

**Integridad**

Una comparación de tamaño y fecha con el estado de cierre de la 5B-3 no muestra cambios en los conjuntos de datos, en las Fases 34–39R, en los protocolos sellados ni en la Tesis. No se borró ningún archivo. No se ejecutaron migraciones sobre bases persistentes ni se modificaron registros.

---

## 10. Conclusión: **lista con restricciones**

**Por qué no es «no lista».** Las funciones están terminadas. Los defectos reproducibles se corrigieron y las pruebas se repitieron sin fallos en Django, JavaScript y Chrome. Las medidas de seguridad autorizadas están implementadas y no requieren migración.

**Por qué no es «lista» sin más.** Quedan restricciones que no se pueden resolver sin autorización, migración o una decisión externa:

1. **Revisión académica:** debe hacerse con datos sintéticos y en una base limpia, porque DR-1 sigue sin resolver.
2. **Participantes reales:** no se debe abrir la plataforma hasta completar la validación clínica y ético-jurídica, rotar los secretos, configurar HTTPS, decidir sobre el cifrado de la base y decidir si B1 se muestra a mujeres reales.
3. **Orientaciones educativas:** deben seguir apagadas hasta validar su catálogo.
4. **Git:** el trabajo existe solo en la copia local y en respaldos del mismo disco hasta que se autorice su incorporación.
