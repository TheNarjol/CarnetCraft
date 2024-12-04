
import imgkit
import os
import platform
import qrcode
import tempfile
from jinja2 import Environment, FileSystemLoader

# Obtener la ruta absoluta de la imagen
imagen_url = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "PLANTILLA.png"
)

class ImageGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader("."))
        self.path_wkhtmltoimage = self.get_wkhtmltoimage_path()

    def get_wkhtmltoimage_path(self):
        """Determina la ruta de wkhtmltoimage según el sistema operativo."""
        if platform.system() == "Windows":
            return os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "wkhtmltox",
                "bin",
                "wkhtmltoimage.exe",
            )
        else:  # Asumir que es Linux
            return "/usr/local/bin/wkhtmltoimage"  # Asegúrate de que wkhtmltoimage esté en el PATH

    def generate_image(self, data_row, tipo_carnet, ruta_imagen):
        # Generar la cadena para el código QR
        qr_data = self.create_qr_code(data_row)
        color = self.get_template(tipo_carnet)
        template = self.env.get_template("carnet_profesional_template.html")
        
        """Genera una imagen a partir de los datos y el tipo de carnet proporcionado."""
        html_out = template.render(
            data_row=data_row, 
            ruta_imagen=ruta_imagen,
            imagen_url=imagen_url, 
            qr_data=qr_data, 
            color=color
        )

        if os.path.exists(ruta_imagen):
            # Cargar la imagen y realizar operaciones   
            print(f"Cargando imagen desde: {ruta_imagen}")  
            # Aquí iría el código para generar la imagen del carnet

        else:
            raise FileNotFoundError(f"La ruta de la imagen no existe: {ruta_imagen}")
    
        options = {
            'width': 283,  # Ancho deseado
            'height': 405,  # Altura deseada (opcional) ,
            'quality': 100,
            "enable-local-file-access": ""
        }

        image_filename = f"{data_row['Cedula']}_{tipo_carnet}.png"

        imgkit.from_string(
            html_out,
            image_filename,
            config=imgkit.config(wkhtmltoimage=self.path_wkhtmltoimage),
            options=options,
        )

        return image_filename

    def create_qr_code(self, data_row):

        """Genera un código QR y lo guarda como imagen en una ubicación temporal."""    
        qr_string = f"Cargo: {data_row['Cargo']}, Cédula: {data_row['Cedula']}, Oficina: {data_row['Adscrito']}"    
        
        qr = qrcode.QRCode( 
            version=1,  
            error_correction=qrcode.constants.ERROR_CORRECT_L,  
            box_size=10,    
            border=4,   
        )   
        qr.add_data(qr_string)  
        qr.make(fit=True)   
        # Crear la imagen del código QR 
        qr_img = qr.make_image(fill_color="black", back_color="white")  
        # Crear un archivo temporal para guardar la imagen del código QR    
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file: 
            qr_code_filename = temp_file.name  # Obtiene el nombre del archivo temporal 
            qr_img.save(qr_code_filename)  # Guarda la imagen en el archivo temporal    
        # Verificar si el archivo se creó correctamente 
        if os.path.exists(qr_code_filename):    
            print(f"El código QR se ha guardado en: {qr_code_filename }")   
        else:   
            print("Error: El archivo QR no se ha creado.")  
        # Devolver la ruta absoluta del archivo 
        return os.path.abspath(qr_code_filename)

    def get_template(self, tipo_carnet):
        """Devuelve el código de color según el tipo de carnet."""
        # Diccionario que asocia tipos de carnet con códigos de color   
        colores = { 
            "Profesional": "#2d29c6",   
            "Gerencial": "#c63b29", 
            "Administrativo": "#c63b29" 
        }   
        # Verificar si el tipo de carnet es válido y devolver el color correspondiente  
        if tipo_carnet in colores:  
            return colores[tipo_carnet] 
        else:   
            raise ValueError("Tipo de carnet no válido.")