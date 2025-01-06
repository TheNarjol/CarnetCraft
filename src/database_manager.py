# database_manager.py
import json
import mysql.connector
from mysql.connector import Error
import pandas as pd

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

    def fetch_data(self, page=1, limit=10):
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
        
    def close_database_connection(self):
        """Cierra la conexión a la base de datos."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión a la base de datos cerrada.")