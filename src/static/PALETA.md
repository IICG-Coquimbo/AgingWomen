# Paleta y estilo visual

Toda la apariencia de la plataforma se controla desde un solo lugar:

    src/static/css/tema.css  →  bloque :root

## Cambiar el color corporativo

En `tema.css`, dentro de `:root`, edita las variables de **PALETA PRINCIPAL**:

| Variable | Para qué se usa |
|---|---|
| `--color-primario` | color base: encabezado, botones, enlaces |
| `--color-primario-oscuro` | hover de botones, títulos |
| `--color-primario-claro` | bordes y foco de campos |
| `--color-primario-suave` | fondo de los recuadros de aviso (`.info`) |
| `--color-acento` | acciones secundarias |

Ejemplo — cambiar el morado por un azul corporativo:

```css
--color-primario: #1d4ed8;
--color-primario-oscuro: #1e3a8a;
--color-primario-claro: #93c5fd;
--color-primario-suave: #eff6ff;
```

No hace falta tocar ningún archivo `.html` ni reiniciar el servidor: basta recargar la página.

## Escala de calor MRS

Las variables `--calor-0` … `--calor-4` definen el degradado verde→rojo de la
escala MRS (Fase 7D). Cambiarlas altera solo esa escala, no el resto del tema.
