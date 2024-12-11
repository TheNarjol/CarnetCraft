import imgkit
import os
import platform
import qrcode
import tempfile
import logging
import os

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
    "PLANTILLA.png"
)

class ImageGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

        # Acceder a la ruta del cargador
        if isinstance(self.env.loader, FileSystemLoader):
            # Obtener la ruta completa
            print("Rutas de búsqueda de plantillas:")
            print(templates_dir)  # Imprxime la ruta completa al directorio de plantillas

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
                    "wkhtmltopdf.exe",
                )
            else:  # Asumir que es Linux
                return "/usr/bin/wkhtmltopdf"  # Asegúrate de que wkhtmltopdf esté en el PATH
        except Exception as e:
            logging.error(f"Error al obtener la ruta de wkhtmltopdf: {str(e)}")
            raise

    def generate_image(self, data_row, tipo_carnet, ruta_imagen):
        """Genera una imagen a partir de los datos y el tipo de carnet proporcionado."""
        try:
            # Validar que data_row contenga los campos necesarios
            required_fields = ['Cedula', 'Cargo', 'Adscrito']
            for field in required_fields:
                if field not in data_row:
                    raise ValueError(f"Falta el campo requerido: {field}")

            # Generar la cadena para el código QR
            qr_data = self.create_qr_code(data_row)
            color = self.get_template(tipo_carnet)
            try:
                template = self.env.get_template("carnet_template.html")
                print("Plantilla cargada con éxito.")
            except TemplateNotFound:
                print("La plantilla no se encontró.")
                logging.error("La plantilla 'carnet_template.html' no se encontró.")
                raise FileNotFoundError("La plantilla de carnet no se pudo encontrar. Asegúrate de que el archivo exista en la ruta correcta.")
            
            # Imprimir las rutas y datos antes de renderizar
            print("Rutas y datos utilizados para renderizar la plantilla:")
            print(f"  - Ruta de la imagen: {ruta_imagen}")
            print(f"  - URL de la imagen: {imagen_url}")
            print(f"  - URL de la imagen QR: {qr_data}")
            
            print(f"  - Datos de la fila: {data_row}")

            try:
                # Intentar renderizar la plantilla
                html_out = template.render(
                    data_row=data_row, 
                    ruta_imagen=ruta_imagen,
                    imagen_url=imagen_url, 
                    qr_data=qr_data, 
                    color=color
                )
                print("Plantilla renderizada con éxito.")
            except Exception as e:
                # Manejo de errores
                logging.error(f"Error al renderizar la plantilla: {str(e)}")
                print(f"Error al renderizar la plantilla: {str(e)}")
                raise  # Vuelve a lanzar la excepción si es necesario

            if not os.path.exists(ruta_imagen):
                raise FileNotFoundError(f"La ruta de la imagen no existe: {ruta_imagen}")

            options = {
                "enable-local-file-access": ""
            }

            image_filename = f"{data_row['Cedula']}_{tipo_carnet}.png"

            imgkit.from_string(
                html_out,
                image_filename,
                config=imgkit.config(wkhtmltoimage=self.path_wkhtmltopdf),
                options=options,
            )
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

    def create_qr_code(self, data_row):
        """Genera un código QR y lo guarda como imagen en una ubicación temporal."""
        try:
            qr_string = f"Cargo: {data_row['Cargo']}, Cédula: {data_row['Cedula']}, Oficina: {data_row['Adscrito']}"    
            
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

    def get_template(self, tipo_carnet):
        """Devuelve el código de color según el tipo de carnet."""
        # Diccionario que asocia tipos de carnet con códigos de color   
        colores = { 
            "Profesional": "#2d29c6",   
            "Gerencial": "#c63b29", 
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
            raise