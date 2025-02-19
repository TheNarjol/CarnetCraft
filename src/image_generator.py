import imgkit
import os
import platform
import qrcode
import tempfile
import io
import logging
import os
import base64
from database_manager import DatabaseManager

from PIL import Image
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


# Obtener la ruta absoluta al directorio de plantillas
project_dir = os.path.dirname(os.path.abspath(__file__))  # Obtiene el directorio del archivo actual
templates_dir = os.path.join(project_dir, "templates")  # Asumiendo que "templates" está en el mismo nivel que "src"


# Configure el logger
logging.basicConfig(
    filename='image_generator.log',  # Nombre del archivo de log
    level=logging.ERROR,              # Nivel de log
    format='%(asctime)s - %(levelname)s - %(message)s'  # Formato del log
)

# Obtener la ruta absoluta de la imagen
imagen_url = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "templates",
    "PLANTILLA.png"
)

class ImageGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.db = DatabaseManager()

        # Acceder a la ruta del cargador
        try:
            # Acceder a la ruta del cargador
            if isinstance(self.env.loader, FileSystemLoader):
                # Obtener la ruta completa
                self.env.loader.searchpath
        except Exception as e:
            print(f"Error al acceder a la ruta del cargador: {str(e)}")

        self.path_wkhtmltopdf = self.get_wkhtmltopdf_path()
        # The `get_wkhtmltopdf_path` method in the provided Python code
            # is responsible for determining the path to the `wkhtmltopdf`
            # executable based on the operating system that the script is
            # running on.

    def get_wkhtmltopdf_path(self):
        """Determina la ruta de wkhtmltopdf según el sistema operativo."""
        try:
            if platform.system() == "Windows":
                return os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "wkhtmltox",
                    "bin",
                    "wkhtmltoimage.exe",
                )
            else:  # Asumir que es Linux
                return "/usr/bin/wkhtmltoimage"  # Asegúrate de que wkhtmltopdf esté en el PATH
        except Exception as e:
            logging.error(f"Error al obtener la ruta de wkhtmltopdf: {str(e)}")
            raise

    def generate_carnet(self, data_row):
        """Genera una imagen a partir de los datos y el tipo de carnet proporcionado."""
        try:
            # Validar que data_row contenga los campos necesarios
            required_fields = ["Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "RutaImagen", "TipoCarnet"]
            for field in required_fields:
                if field not in data_row:
                    raise ValueError(f"Falta el campo requerido: {field}")

            # Generar la cadena para el código QR
            color = self.get_template(data_row['TipoCarnet'])
            try:
                id_trabajador = self.db.fetch_id_by_cedula(data_row['Cedula'])
            except Exception as e:
                print(f"Error al obtener el ID del trabajador: {e}")
                id_trabajador = None
            
            last_carnet = self.db.feth_last_carnet(id_trabajador)
            if not self.db.check_fecha_emision_expiracion(last_carnet):
                self.db.save_carnet(id_trabajador)
                new_carnet =  self.db.feth_last_carnet(id_trabajador)
            else:
                new_carnet = last_carnet

            try:
                template = self.env.get_template("carnet_template.html")
            except TemplateNotFound:
                print("La plantilla no se encontró.")
                logging.error("La plantilla 'carnet_template.html' no se encontró.")
                raise FileNotFoundError("La plantilla de carnet no se pudo encontrar. Asegúrate de que el archivo exista en la ruta correcta.")
            
            try:
                blob = self.convertir_str_a_bytes(data_row['RutaImagen'])
                temp_photo_path = self.create_temp_photo_from_blob(blob)
                print(f"Foto temporal creada en: {temp_photo_path}")
            except Exception as e:
                print(f"Error al crear la foto temporal: {str(e)}")
                raise  # Relanzar la excepción para manejarla en el bloque externo


            try:
                qr_data = self.create_qr_code(data_row, new_carnet)
                # Intentar renderizar la plantilla
                html_out = template.render(
                    data_row=data_row, 
                    ruta_imagen=temp_photo_path,
                    imagen_url=imagen_url, 
                    qr_data=qr_data, 
                    color=color,
                    carnet=new_carnet
                )
            except Exception as e:
                # Manejo de errores
                logging.error(f"Error al renderizar la plantilla: {str(e)}")
                print(f"Error al renderizar la plantilla: {str(e)}")
                raise  # Vuelve a lanzar la excepción si es necesario

            if not os.path.exists(temp_photo_path):
                raise FileNotFoundError(f"La ruta de la imagen no existe: {temp_photo_path}")

            
            
            options = {
                "enable-local-file-access": "",
                "width": 804,  # Establecer el ancho de la imagen
                "disable-smart-width": "",  # Deshabilitar el ajuste automático de ancho
            }

            image_filename = f"{data_row['Cedula']}_{data_row['TipoCarnet']}.png"
            print(image_filename)
            if os.path.exists(image_filename):
                os.remove(image_filename)

            imgkit.from_string(
                html_out,
                image_filename,
                config=imgkit.config(wkhtmltoimage=self.path_wkhtmltopdf),
                options=options,
            )
            os.remove(temp_photo_path)
            return image_filename

        except FileNotFoundError as fnf_error:
            logging.error(f"Archivo no encontrado: {str(fnf_error)}")
            raise
        except ValueError as ve:
            logging.error(f"Error de valor: {str(ve)}")
            raise
        except Exception as e:
            logging.error(f"Error al generar la imagen: {str(e)}")
            raise

    def create_qr_code(self, data_row, carnet):
        """Genera un código QR y lo guarda como imagen en una ubicación temporal."""
        try:
            qr_string = f"V-{data_row['Cedula']} \n{data_row['Nombre']}. {data_row['Apellidos']}. \n\n{data_row['Cargo']} \n{data_row['Adscrito']} \n\nEn caso de Emergencia, Perdida, Extravio, Hurto o Robo Debe de Notificar a la oficina de tecnologia de la informacion \n(212) 351 0822 \n\nFUNDALANAVIAL"    
            qr_string = qr_string.upper()
            qr = qrcode.QRCode( 
                version=1,  
                error_correction=qrcode.constants.ERROR_CORRECT_L,  
                box_size=10,    
                border=4,   
            )   
            qr.add_data(qr_string)  
            qr.make(fit=True)   
            qr_img = qr.make_image(fill_color="black", back_color="white")  
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file: 
                qr_code_filename = temp_file.name  
                qr_img.save(qr_code_filename)  
            
            if not os.path.exists(qr_code_filename):    
                raise FileNotFoundError("Error: El archivo QR no se ha creado correctamente.")

            return qr_code_filename

        except Exception as e:
            logging.error(f"Error al crear el código QR: {str(e)}")
            raise
    
    def convertir_str_a_bytes(self, binary_str):
        """
        Convierte una cadena que contiene datos binarios en bytes.

        Args:
            binary_str (str): Cadena que contiene datos binarios.

        Returns:
            bytes: Datos binarios.
        """
        try:
            return binary_str.encode('latin1')  # Usar 'latin1' para preservar los bytes
        except Exception as e:
            print(f"Error al convertir la cadena a bytes: {str(e)}")
            raise    
    
    def create_temp_photo_from_blob(self, blob_data):
        """
        Crea una foto temporal a partir de datos en formato blob.

        Args:
            blob_data (bytes): Datos de la imagen en formato blob.

        Returns:
            str: Ruta del archivo temporal generado.

        Raises:
            ValueError: Si los datos blob están vacíos o no son válidos.
            Exception: Si ocurre un error al procesar la imagen.
        """
        try:
            # Verificar si los datos blob están vacíos o no son válidos
            if not blob_data:
                raise ValueError("Los datos blob están vacíos o no son válidos.")

            # Crear un archivo temporal para guardar la imagen
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_file_path = temp_file.name

                # Convertir los datos blob en una imagen y guardarla
                image = Image.open(io.BytesIO(blob_data))
                image.save(temp_file_path, format='PNG')

                # Verificar si el archivo se creó correctamente
                if not os.path.exists(temp_file_path):
                    raise FileNotFoundError("No se pudo crear el archivo temporal de la imagen.")

                return temp_file_path

        except Exception as e:
            logging.error(f"Error al crear la foto temporal desde blob: {str(e)}")
            raise
        
    def get_template(self, tipo_carnet):
        """Devuelve el código de color según el tipo de carnet."""
        # Diccionario que asocia tipos de carnet con códigos de color   
        colores = { 
            "Profesional": "#2d29c6",   
            "Gerencial": "#ff0000",
            "Coordinadores": "#E08343",
            "Obrero": "#00913f",
            "Seguridad": "#757575",
            "Administrativo": "#c63b29" 
        }   
        # Verificar si el tipo de carnet es válido y devolver el color correspondiente
        try:    
            if tipo_carnet in colores:  
                return colores[tipo_carnet] 
            else:   
                raise ValueError("Tipo de carnet no válido.")
        except Exception as e:
            logging.error(f"Error al obtener el template: {str(e)}")
            print(str(e))
            print(tipo_carnet)
            raise e