# Generador De Carnets

## Descripción
Generador De Carnets es una herramienta diseñada para crear carnets para trabajadores, diferenciándolos en tres tipos: Administrativo, Gerencial y Profesional. Esta aplicación es una solicitud a la Oficina de TI y tiene como objetivo simplificar el proceso de generación de carnets, evitando la necesidad de hacerlo manualmente y llevando un registro de los carnets emitidos y sus fechas.

## Instalación
Para instalar y ejecutar el proyecto, asegúrate de tener instalado Python 3.10.15 y wkhtmltox 0.12.6. Puedes guardar wkhtmltox en el mismo directorio que el script.

1. Clona este repositorio en tu máquina local.
2. Asegúrate de tener Python 3.10.15 instalado.
3. Descarga wkhtmltox 0.12.6 y colócalo en el mismo directorio que el script.

## Uso
Para ejecutar el generador de carnets, dirígete al directorio donde se encuentra el script y ejecuta el siguiente comando:

```bash
python Generador.py data.xlsx
```
Donde data.xlsx debe contener las siguientes columnas:

- Nombre
- Apellidos
- Cédula
- Adscrito
- Cargo
- Tipo
E
## Licencia
Este proyecto está bajo la Licencia MIT.ste comando generará un archivo PDF con la estructura cedula_tipo.pdf, donde cedula es el número de cédula y tipo es el tipo de carnet.
