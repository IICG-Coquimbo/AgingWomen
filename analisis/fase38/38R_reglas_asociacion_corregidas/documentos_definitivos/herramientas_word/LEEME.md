# Herramientas para generar los documentos de 38R y 39R

## Instalación del paquete de Word

Requiere Node.js. Desde esta carpeta:

```
npm ci
```

Instala exactamente `docx` 9.15.2 según `package-lock.json`. La carpeta `node_modules/` no entra en el control de versiones (`.gitignore`).

Los generadores no usan ninguna carpeta temporal: `scripts/entorno_word.py` fija `NODE_PATH` en `herramientas_word/node_modules` y detiene la generación con un mensaje claro si falta el paquete.

## Bibliotecas de Python para figuras y validación

Están registradas en `requirements-documentos.txt`, junto con las versiones de Python, Node y npm usadas. Son solo para esta generación documental; no modifican las dependencias de los análisis ni de la plataforma.

## Regenerar

Desde `documentos_definitivos/scripts/`:

```
python -B figuras_38r.py [prefijos, por ejemplo f01 f07]
python -B generar_documentos_38r.py [números, por ejemplo 03 04]
```

Para la 39R, los mismos pasos con `figuras_39r.py` y `generar_documentos_39r.py`, desde su carpeta `scripts/`. Sin argumentos se regenera todo.

## Controlar

- `python -B validar_documentos.py`, desde `scripts/` de la 38R: cifras, columnas, jerarquía, referencias y protocolos.
- `control_maquetacion.ps1`: requiere Microsoft Word. Trabaja solo con copias en la carpeta que se indique y exporta allí los PDF:

```
powershell -File control_maquetacion.ps1 -Documentos <carpeta word> -Temporal <carpeta temporal> -SalidaCsv <validacion\control_maquetacion.csv>
```
