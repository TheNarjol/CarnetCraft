# database_manager.py
import json
import mysql.connector
from mysql.connector import Error
import pandas as pd
from funcion import convertir_imagen_a_binario
from datetime import datetime, timedelta
import re

class DatabaseManager:
    def __init__(self):
        self.set_connection_details()
        self.connect_to_database()
        self.tabla_empleados = "trabajadores"
        self.tabla_oficina = "oficinas"
        self.table_carnet = "carnets"

    def create_tables(self):
        """
        Crea las tablas en la base de datos si no existen.
        """
        try:
            cursor = self.connection.cursor()

            # Crear la tabla de oficinas si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oficinas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    nomenclatura VARCHAR(50) NOT NULL UNIQUE
                )
            """)

            # Crear la tabla de trabajadores si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trabajadores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    apellidos VARCHAR(255) NOT NULL,
                    cedula VARCHAR(50) NOT NULL UNIQUE,
                    adscrito VARCHAR(255) NOT NULL,
                    cargo VARCHAR(255) NOT NULL,
                    imagen LONGBLOB,
                    tipo_carnet VARCHAR(50) NOT NULL
                )
            """)
            
            # Crear la tabla de carnets si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS carnets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_trabajador INT NOT NULL,
                    fecha_emision DATE NOT NULL,
                    fecha_expiracion DATE NOT NULL,
                    correlativo VARCHAR(50) NOT NULL UNIQUE,
                    FOREIGN KEY (id_trabajador) REFERENCES trabajadores(id)  -- Relación con la tabla de trabajadores
                )
            """)

            # Confirmar los cambios
            self.connection.commit()
            cursor.close()
            print("Tablas creadas o verificadas correctamente.")
        except Error as e:
            print(f"Error al crear las tablas: {e}")
    
    def set_connection_details(self):
        """Establece los detalles de conexión a la base de datos."""
        with open('settings.json') as f:
            settings = json.load(f)
        self.host = settings['mysql_host']
        self.database = settings['mysql_db']
        self.user = settings['mysql_user']
        self.password = settings['mysql_pass']

    def connect_to_database(self):
        """Establece la conexión a la base de datos."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                collation='utf8mb4_general_ci'
            )
        except Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            self.connection = None
    
    def generar_correlativo(self, id_trabajador):
        """
        Genera un correlativo único basado en el id_trabajador y su adscripción.

        Parámetros:
        - id_trabajador (int): ID del trabajador para el cual se generará el correlativo.

        Retorna:
        - correlativo (str): Correlativo único en el formato "ADSCRIPCION-ID_TRABAJADOR-INCREMENTAL".
        """
        try:
            cursor = self.connection.cursor()

            # Obtener la adscripción del trabajador
            query_adscrito = f"SELECT adscrito FROM {self.tabla_empleados} WHERE id = %s"
            cursor.execute(query_adscrito, (id_trabajador,))
            resultado_adscrito = cursor.fetchone()

            if not resultado_adscrito:
                raise ValueError("No se encontró el trabajador con el ID proporcionado.")

            adscrito = resultado_adscrito[0]  # Obtener la adscripción

            # Obtener el último correlativo para esa adscripción
            query_correlativo = f"""
                SELECT correlativo FROM {self.table_carnet}
                WHERE id_trabajador IN (
                    SELECT id FROM {self.tabla_empleados} WHERE adscrito = %s
                )
                ORDER BY correlativo DESC
                LIMIT 1
            """
            cursor.execute(query_correlativo, (adscrito,))
            ultimo_correlativo = cursor.fetchone()

            if ultimo_correlativo:
                # Extraer el número incremental del último correlativo
                correlativo_str = ultimo_correlativo[0]
                
                # Usar una expresión regular para separar la parte alfabética y la numérica
                match = re.match(r"([A-Za-z]+)(\d{4})$", correlativo_str)
                if match:
                    letras = match.group(1)  # Parte alfabética
                    numero = int(match.group(2))  # Parte numérica como entero
                    
                    # Incrementar el número
                    incremental = numero + 1
                    
            else:
                # Si no hay correlativos previos, empezar desde 1
                incremental = 1

            # Generar el nuevo correlativo
            correlativo = f"{adscrito}{incremental:04d}"


            return correlativo

        except Error as e:
            print(f"Error al generar el correlativo: {e}")
            return None
        finally:
            cursor.close()
    
    def fetch_data_all(self):
        """Consulta datos de la base de datos y los devuelve como un DataFrame."""
        if self.connection is None:
            print("No hay conexión a la base de datos.")
            return None

        query = f"SELECT nombre, apellidos,cedula, adscrito, cargo, imagen, tipo_carnet FROM {self.tabla_empleados}"
        
        try:
            df = pd.read_sql(query, self.connection)
            return df
        
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return None

    def fetch_data(self, adscrito=None, tipo=None, page=1):
        limit = 25
        offset = (page - 1) * limit
        if adscrito and tipo:
            query = f"SELECT nombre, apellidos, cedula, adscrito, cargo, imagen, tipo_carnet FROM {self.tabla_empleados} WHERE adscrito = '{adscrito}' AND tipo_carnet = '{tipo}' LIMIT {limit} OFFSET {offset}"
        elif adscrito:
            query = f"SELECT nombre, apellidos, cedula, adscrito, cargo, imagen, tipo_carnet FROM {self.tabla_empleados} WHERE adscrito = '{adscrito}' LIMIT {limit} OFFSET {offset}"
        elif tipo:
            query = f"SELECT nombre, apellidos, cedula, adscrito, cargo, imagen, tipo_carnet FROM {self.tabla_empleados} WHERE tipo_carnet = '{tipo}' LIMIT {limit} OFFSET {offset}"
        else:
            query = f"SELECT nombre, apellidos, cedula, adscrito, cargo, imagen, tipo_carnet FROM {self.tabla_empleados} LIMIT {limit} OFFSET {offset}"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            resultado = cursor.fetchall()
            cursor.close()
            return resultado
        except Error as e:
            print(f"Error al obtener datos: {e}")
            return None
    
    def fetch_data_by_cedula(self, cedula):
        query = f"SELECT nombre, apellidos, cedula, adscrito, cargo, imagen, tipo_carnet FROM {self.tabla_empleados} WHERE cedula = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (cedula,))
            resultado = cursor.fetchone()
            cursor.close()
            return resultado
        except Error as e:
            print(f"Error al obtener datos: {e}")
            return None
    
    def fetch_id_by_cedula(self, cedula):
        """
        Obtiene el ID de un trabajador según su cédula.

        Parámetros:
        - cedula (str): Cédula del trabajador.

        Retorna:
        - id_trabajador (int): ID del trabajador si se encuentra, None en caso contrario.
        """
        try:
            cursor = self.connection.cursor()

            # Obtener el ID del trabajador según la cédula
            query = f"SELECT id FROM {self.tabla_empleados} WHERE cedula = %s"
            cursor.execute(query, (cedula,))
            resultado = cursor.fetchone()

            if resultado:
                id_trabajador = resultado[0]
                return id_trabajador
            else:
                return None

        except Error as e:
            print(f"Error al obtener el ID por cédula: {e}")
            return None
        finally:
            cursor.close()

    def fetch_oficinas_with_id(self):
        """
        Obtiene una lista de oficinas desde la tabla de oficinas, incluyendo el ID.

        Retorna:
        - Una lista de tuplas en el formato [(id, nombre, codigo), ...].
        """
        query = f"SELECT * FROM {self.tabla_oficina}"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            resultado = cursor.fetchall()
            cursor.close()
            return resultado
        except Error as e:
            print(f"Error al obtener la lista de oficinas: {e}")
            return []
    
    def fetch_oficinas(self):
        """
        Obtiene una lista de oficinas desde la tabla de oficinas.

        Retorna:
        - Una lista de tuplas en el formato [(nombre_oficina, codigo_oficina), ...].
        """
        query = f"SELECT nombre, nomenclatura FROM {self.tabla_oficina}"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            resultado = cursor.fetchall()
            cursor.close()
            return resultado
        except Error as e:
            print(f"Error al obtener la lista de oficinas: {e}")
            return []
    
    def get_total_filas(self):
        """Obtiene el número total de filas en la tabla carnets."""
        query = f"SELECT COUNT(*) AS total_filas FROM {self.tabla_empleados}"
        cursor = self.connection.cursor()
        cursor.execute(query)
        resultado = cursor.fetchone()
        cursor.close()
        return resultado[0]

    def save_new_entry(self, data):
        """
        Guarda una nueva entrada en la base de datos.

        Parámetros:
        - data (dict): Diccionario con los datos de la nueva entrada.
            Debe contener las siguientes claves:
                - nombre
                - apellidos
                - cedula
                - adscrito
                - cargo
                - imagen (datos de la imagen en binario)
                - tipo_carnet

        Retorna:
        - True si la entrada se guardó correctamente, False en caso contrario.
        """
        query = f"INSERT INTO {self.tabla_empleados} (nombre, apellidos, cedula, adscrito, cargo, imagen, tipo_carnet) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (
                data['nombre'],
                data['apellidos'],
                data['cedula'],
                data['adscrito'],
                data['cargo'],
                data['imagen'], 
                data['tipo_carnet']
            ))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error al guardar la entrada: {e}")
            return False

    def feth_last_carnet(self, id_trabajador):
        """
        Obtiene el último carnet hecho según el trabajador.

        Parámetros:
        - id_trabajador (int): ID del trabajador.

        Retorna:
        - carnet (dict): Diccionario con los datos del último carnet.
        last_carnet = {
            "id": id_carnet,
            "id_trabajador": id_trabajador,
            "fecha_emision": fecha_emision,
            "fecha_expiracion": fecha_expiracion,
            "correlativo": correlativo
        }
        """
        try:
            cursor = self.connection.cursor()

            # Obtener el último carnet para el trabajador
            query = f"""
                SELECT * FROM {self.table_carnet}
                WHERE id_trabajador = %s
                ORDER BY fecha_emision DESC
                LIMIT 1
            """
            cursor.execute(query, (id_trabajador,))
            ultimo_carnet = cursor.fetchone()

            if not ultimo_carnet:
                return None

            # Crear un diccionario con los datos del carnet
            carnet = {
                "id": ultimo_carnet[0],
                "id_trabajador": ultimo_carnet[1],
                "fecha_emision": ultimo_carnet[2],
                "fecha_expiracion": ultimo_carnet[3],
                "correlativo": ultimo_carnet[4]
            }

            return carnet

        except Error as e:
            print(f"Error al obtener el último carnet: {e}")
            return None
        finally:
            cursor.close()
    
    def save_carnet(self, id_trabajador, periodo_tiempo=365):
        """
        Inserta un nuevo carnet en la base de datos.

        Parámetros:
        - id_trabajador (int): ID del trabajador.
        - periodo_tiempo (int): Período de tiempo en días (por defecto, 365 días).

        Retorna:
        - True si el carnet se insertó correctamente, False en caso contrario.
        """
        try:
            cursor = self.connection.cursor()

            # Obtener la fecha actual del servidor SQL
            query = "SELECT NOW()"
            cursor.execute(query)
            fecha_actual = cursor.fetchone()[0]

            # Calcular la fecha de expiración
            fecha_expiracion = fecha_actual + timedelta(days=periodo_tiempo)

            # Generar el correlativo único
            correlativo = self.generar_correlativo(id_trabajador)

            # Insertar el nuevo carnet
            query = f"""
                INSERT INTO {self.table_carnet} (id_trabajador, fecha_emision, fecha_expiracion, correlativo)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (id_trabajador, fecha_actual, fecha_expiracion, correlativo))

            # Confirmar los cambios
            self.connection.commit()
            cursor.close()
            return True

        except Error as e:
            print(f"Error al insertar el carnet: {e}")
            return False   
    
    def save_oficina(self, nombre_oficina, codigo_oficina):
        """
        Guarda una nueva oficina en la base de datos.

        Parámetros:
        - nombre_oficina (str): Nombre de la oficina.
        - codigo_oficina (str): Código único de la oficina.

        Retorna:
        - True si la oficina se guardó correctamente, False en caso contrario.
        """
        query = f"INSERT INTO {self.tabla_oficina} (nombre, nomenclatura) VALUES (%s, %s)"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (nombre_oficina, codigo_oficina))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error al guardar la oficina: {e}")
            return False
    
    def update_entry(self, new_values):
        query = f"UPDATE {self.tabla_empleados} SET nombre = %s, apellidos = %s, adscrito = %s, cargo = %s, imagen = %s, tipo_carnet = %s WHERE cedula = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (
                new_values['nombre'],
                new_values['apellidos'],
                new_values['adscrito'],
                new_values['cargo'],
                new_values['imagen'],
                new_values['tipo_carnet'],
                new_values['cedula']
            ))
            self.connection.commit()
        except Error as e:
            print(f"Error al modificar el registro: {e}")
    
    def update_oficina(self, id_oficina, nuevo_nombre, nuevo_codigo):
        """
        Modifica una oficina existente en la base de datos usando su ID.

        Parámetros:
        - id_oficina (int): ID de la oficina a modificar.
        - nuevo_nombre (str): Nuevo nombre para la oficina.
        - nuevo_codigo (str): Nuevo código para la oficina.

        Retorna:
        - True si la oficina se modificó correctamente, False en caso contrario.
        """
        query = f"UPDATE {self.tabla_oficina} SET nombre = %s, nomenclatura = %s WHERE id = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (nuevo_nombre, nuevo_codigo, id_oficina))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error al modificar la oficina: {e}")
            return False
    
    def delete_oficina(self, id_oficina):
        """
        Elimina una oficina de la base de datos usando su ID.

        Parámetros:
        - id_oficina (int): ID de la oficina a eliminar.

        Retorna:
        - True si la oficina se eliminó correctamente, False en caso contrario.
        """
        query = f"DELETE FROM {self.tabla_oficina} WHERE id = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (id_oficina,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error al eliminar la oficina: {e}")
            return False
    
    def delete_oficina(self, codigo_oficina):
        """
        Elimina una oficina de la base de datos.

        Parámetros:
        - codigo_oficina (str): Código único de la oficina a eliminar.

        Retorna:
        - True si la oficina se eliminó correctamente, False en caso contrario.
        """
        query = f"DELETE FROM {self.tabla_oficina} WHERE id = %s "
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (codigo_oficina,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error al eliminar la oficina: {e}")
            return False
    
    def check_duplicate_by_cedula(self, cedula):
        """
        Verifica si ya existe un registro con la misma cédula en la base de datos.

        Parámetros:
        - cedula (str): La cédula a verificar.

        Retorna:
        - True si ya existe un registro con la misma cédula, False en caso contrario.
        """
        query = f"SELECT COUNT(*) FROM {self.tabla_empleados} WHERE cedula = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (cedula,))
            resultado = cursor.fetchone()
            cursor.close()
            return resultado[0] > 0  # Retorna True si hay al menos un registro con la misma cédula
        except Error as e:
            print(f"Error al verificar duplicados: {e}")
            return False

    def check_fecha_emision_expiracion(self, last_carnet):
        """
        Comprueba si la hora del servidor SQL está entre las fechas de emisión y expiración del último carnet.

        Parámetros:
        - last_carnet (dict): Diccionario con los datos del último carnet.

        Retorna:
        - True si la hora del servidor SQL está entre las fechas de emisión y expiración, False en caso contrario.
        """
        if last_carnet is None:
            print("No se encontró el último carnet.")
            return False

        try:
            cursor = self.connection.cursor()

            # Obtener la hora actual del servidor SQL
            query = "SELECT NOW()"
            cursor.execute(query)
            hora_actual = cursor.fetchone()[0]

            # Convertir last_carnet['fecha_emision'] y last_carnet['fecha_expiracion'] a objetos de tipo datetime.datetime
            fecha_emision = datetime.combine(last_carnet['fecha_emision'], datetime.min.time())
            fecha_expiracion = datetime.combine(last_carnet['fecha_expiracion'], datetime.min.time())

            # Comprobar si la hora actual está entre las fechas de emisión y expiración
            if fecha_emision <= hora_actual <= fecha_expiracion:
                return True
            else:
                return False

        except Error as e:
            print(f"Error al comprobar la fecha de emisión y expiración: {e}")
            return False
        finally:
            cursor.close()
                
    def close_database_connection(self):
        """Cierra la conexión a la base de datos."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión a la base de datos cerrada.")
    
    def delete_entry(self, cedula):
        """
        Elimina un registro de trabajador de la base de datos usando su cédula.
        Parámetros:
        - cedula (str): La cédula del trabajador a eliminar.
        Retorna:
        - True si el registro se eliminó correctamente, False en caso contrario.
        """
        try:
            id_trabajador = self.fetch_id_by_cedula(cedula)
            if id_trabajador is None:
                print("No se encontró el trabajador con la cédula proporcionada.")
                return False

            # Eliminar los registros en la tabla carnets relacionados con el trabajador
            self.delete_related_carnets(id_trabajador)

            # Ahora eliminar el trabajador
            self.delete_trabajador(cedula)

            return True

        except Error as e:
            print(f"Error al eliminar el registro: {e}")
            return False

    def delete_related_carnets(self, id_trabajador):
        """
        Elimina los registros en la tabla carnets relacionados con el trabajador.
        Parámetros:
        - id_trabajador (int): ID del trabajador.
        """
        try:
            cursor = self.connection.cursor()
            delete_carnets_query = f"DELETE FROM {self.table_carnet} WHERE id_trabajador = %s"
            cursor.execute(delete_carnets_query, (id_trabajador,))
            self.connection.commit()
            cursor.close()
        except Error as e:
            print(f"Error al eliminar los carnets relacionados: {e}")

    def delete_trabajador(self, cedula):
        """
        Elimina un trabajador de la base de datos usando su cédula.
        Parámetros:
        - cedula (str): La cédula del trabajador a eliminar.
        """
        try:
            cursor = self.connection.cursor()
            delete_trabajador_query = f"DELETE FROM {self.tabla_empleados} WHERE cedula = %s"
            cursor.execute(delete_trabajador_query, (cedula,))
            self.connection.commit()
            cursor.close()
        except Error as e:
            print(f"Error al eliminar el trabajador: {e}")
    
    def fetch_data_by_cedula(self, cedula):
        query = f"SELECT * FROM {self.tabla_empleados} WHERE cedula = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (cedula,))
            resultado = cursor.fetchone()
            cursor.close()
            return resultado
        except Error as e:
            print(f"Error al obtener datos por cédula: {e}")
            return None