# Generador De Carnets

## Descripción
Generador De Carnets es una herramienta diseñada para crear carnets para trabajadores, diferenciándolos en tres tipos: Administrativo, Gerencial y Profesional. Esta aplicación es una solicitud a la Oficina de TI y tiene como objetivo simplificar el proceso de generación de carnets, evitando la necesidad de hacerlo manualmente y llevando un registro de los carnets emitidos y sus fechas.

## Instalación
Para instalar y ejecutar el proyecto, asegúrate de tener instalado Python 3.10.15 y wkhtmltox 0.12.6. Puedes guardar wkhtmltox en el mismo directorio que el script.

1. Clona este repositorio en tu máquina local.
2. Asegúrate de tener Python 3.10.15 instalado.
3. Descarga wkhtmltox 0.12.6 y colócalo en el mismo directorio que el script.
4. Instala las dependencias ejecutando el siguiente comando:

    ```bash
    pip install -r requirements.txt
    ```

## SQL
CREATE DATABASE carnets_db;
USE carnets_db;

CREATE TABLE oficinas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    nomenclatura VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE trabajadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) NOT NULL UNIQUE,
    id_oficina INT NOT NULL,
    cargo VARCHAR(100) NOT NULL,
    tipo_cargo VARCHAR(50) NOT NULL,
    foto BLOB,  -- Para almacenar la foto como un archivo binario
    FOREIGN KEY (id_oficina) REFERENCES oficinas(id)  -- Relación con la tabla de oficinas

);

CREATE TABLE carnets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_trabajador INT NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_expiracion DATE NOT NULL,
    correlativo INT NOT NULL UNIQUE,
    FOREIGN KEY (id_trabajador) REFERENCES trabajadores(id)  -- Relación con la tabla de trabajadores
);

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
Este proyecto está bajo la GNU General Public License (GPL)