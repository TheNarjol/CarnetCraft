import imgkit
import os
import platform
from jinja2 import Environment, FileSystemLoader

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

    def generate_image(self, data_row, tipo_carnet):
        """Genera una imagen a partir de los datos y el tipo de carnet proporcionado."""
        template = self.get_template(tipo_carnet)
        html_out = template.render(data_row=data_row)
        options = {
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

    def get_template(self, tipo_carnet):
        """Selecciona la plantilla según el tipo de carnet."""
        if tipo_carnet == "Profesional":
            return self.env.get_template("carnet_profesional_template.html")
        elif tipo_carnet == "Gerencial":
            return self.env.get_template("carnet_gerencial_template.html")
        elif tipo_carnet == "Administrativo":
            return self.env.get_template("carnet_administrativo_template.html")
        else:
            raise ValueError("Tipo de carnet no válido.")