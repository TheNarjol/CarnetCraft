# database_manager.py
import json
import mysql.connector
from mysql.connector import Error
import pandas as pd
from funcion import convertir_imagen_a_binario

class DatabaseManager:
    def __init__(self):
        self.set_connection_details()
        self.connect_to_database()
        self.tabla_empleados = "carnets"
        self.tabla2 = "nombre_tabla2"

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
            
            if self.connection.is_connected():
                print("Conexión exitosa a la base de datos")
        except Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            self.connection = None
    
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

    def fetch_data(self, page=1, limit=25):
        """Consulta datos de la base de datos y los devuelve como un DataFrame."""
        if self.connection is None:
            print("No hay conexión a la base de datos.")
            return None

        offset = (page - 1) * limit
        query = f"SELECT nombre, apellidos, cedula, adscrito, cargo, imagen, tipo_carnet FROM {self.tabla_empleados} LIMIT {limit} OFFSET {offset}"
        
        try:
            df = pd.read_sql(query, self.connection)
            return df
        
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return None
    
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
    
    def delete_entry(self, cedula):
        query = f"DELETE FROM {self.tabla_empleados} WHERE cedula = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (cedula,))
            self.connection.commit()
        except Error as e:
            print(f"Error al eliminar el registro: {e}")
    
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

    def close_database_connection(self):
        """Cierra la conexión a la base de datos."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión a la base de datos cerrada.")
    
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