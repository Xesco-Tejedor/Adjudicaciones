# Adjudicaciones

Herramienta web para explorar adjudicaciones de contratación pública relacionadas con cultura, archivos, bibliotecas, digitalización y preservación documental. Permite identificar empresas adjudicatarias y organizar una lista de seguimiento.

No es un portal de empleo: una adjudicación no demuestra que una empresa esté contratando. La app no busca contactos ni envía mensajes.

[Abrir la aplicación](https://xesco-tejedor.github.io/Adjudicaciones/) · [Repositorio](https://github.com/Xesco-Tejedor/Adjudicaciones)

## Qué puedes hacer

- Consultar Catalunya, España o ambas fuentes.
- Filtrar por periodo, temas, palabra del objeto del contrato e importe mínimo.
- Ver adjudicatario, NIF cuando está disponible, organismo, importe sin IVA y enlace a la publicación oficial.
- Agrupar las adjudicaciones por empresa y ordenar por número de contratos, importe total o nombre.
- Guardar empresas con estado, etiquetas y notas.
- Exportar las empresas guardadas a CSV, hacer una copia JSON, importarla o imprimir un informe.

## Cómo usarla

1. Abre la aplicación en un navegador con conexión a internet. La búsqueda inicial se ejecuta al cargar la página.
2. Elige el ámbito territorial y el periodo. El valor inicial es Catalunya + España y los últimos 90 días.
3. Activa los temas que te interesan. Si desactivas todos, la búsqueda vuelve a usar todos los temas.
4. Añade, si lo necesitas, una palabra del objeto del contrato y un importe mínimo. Pulsa **Buscar**.
5. Revisa los resultados y abre **Ver publicación oficial** antes de tomar decisiones.
6. En **Empresas**, filtra por empresa o NIF y revisa sus contratos. Pulsa **Guardar empresa** para añadirla a tu seguimiento.
7. En **Guardadas**, cambia el estado a Pendiente, Interesante, Contactada o Descartada, añade etiquetas separadas por comas y escribe notas.
8. Usa **Exportar CSV** para trabajar con la lista en una hoja de cálculo y **Copia de seguridad** para conservar los datos en JSON. **Importar copia** incorpora los registros al navegador actual; las claves coincidentes pueden sustituirse.

## Fuentes y límites

Catalunya se consulta mediante el conjunto de datos abiertos de contratación pública de la Generalitat. España se carga desde `data/es.json`, generado a partir de fuentes Atom de la Plataforma de Contratación del Sector Público.

El repositorio tiene una actualización programada de España cada hora. Es una programación, no una garantía de actualización puntual: revisa la fecha que muestra la app. La carga inicial del histórico estatal y sus límites de descarga tampoco garantizan cobertura completa del periodo elegido.

La clasificación usa códigos CPV y palabras clave; puede omitir contratos relevantes o incluir otros que no lo sean. La consulta de Catalunya está limitada a las 1.500 adjudicaciones más recientes que cumplen los filtros. Si una fuente falla, la consulta conjunta puede mostrar solo la otra y un aviso.

Los importes mostrados son sin IVA. Los recuentos y sumas describen los resultados cargados, no toda la actividad de una empresa. Algunos registros pueden identificarla únicamente por NIF.

## Datos guardados

Las empresas, estados, etiquetas y notas se guardan en el almacenamiento local del navegador. No hay cuenta ni sincronización entre dispositivos. Borrar los datos del sitio, cambiar de navegador o usar otra dirección de la app puede dejar esa lista fuera de alcance. Exporta copias periódicas.

Consultar las fuentes externas requiere conexión. Las notas y los estados no se envían a las plataformas de contratación mediante el código de esta app.

## Ejecutarla en local

La interfaz está en `index.html`; los datos estatales están en `data/es.json`. Para servir una copia del repositorio con Python 3:

```bash
git clone https://github.com/Xesco-Tejedor/Adjudicaciones.git
cd Adjudicaciones
python3 -m http.server 8000
```

Abre `http://localhost:8000`. La búsqueda de Catalunya sigue necesitando acceso a su fuente externa. El proceso estatal está en `scripts/fetch_es.py` y su programación en `.github/workflows/es.yml`; no se ejecuta por abrir la interfaz local.
