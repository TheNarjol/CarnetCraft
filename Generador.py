"""
Generar Carnets en PDF a partir de datos incluidos en varios DataFrames de Pandas
Desarrollado por theNarjol
"""

from __future__ import print_function
import pandas as pd
import argparse
from jinja2 import Environment, FileSystemLoader
import pdfkit  # Importar PDFKit
import os

def generate_pdf(data_row, template, config):
    """
    Generar un archivo PDF a partir de una fila de datos y una plantilla HTML.

    Args:
        data_row (Series): La fila de datos que contiene la información del carnet.
        template (Template): La plantilla Jinja2 utilizada para generar el HTML.
        config: Configuración de pdfkit.

    Returns:
        str: El nombre del archivo PDF generado.
    """
    # Renderizar el HTML con los datos de la fila
    html_out = template.render(data_row=data_row)

    # Crear el nombre del archivo PDF
    pdf_filename = f"{data_row['Cedula']}_{data_row['Tipo']}.pdf"
    
    # Generar el PDF utilizando PDFKit
    pdfkit.from_string(html_out, pdf_filename, configuration=config, options={"enable-local-file-access": None})

    return pdf_filename

if __name__ == "__main__":
    # Configurar el analizador de argumentos para permitir la entrada de archivos
    parser = argparse.ArgumentParser(description='Generar carnets PDF')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help="archivo fuente del informe en Excel")
    args = parser.parse_args()

    # Leer el archivo y asegurarse de que tiene la estructura correcta
    df = pd.read_excel(args.infile.name)  # Leer el archivo Excel en un DataFrame

    # Verificar que las columnas requeridas están presentes
    required_columns = ['Nombre', 'Apellidos', 'Cedula', 'Adscrito', 'Cargo', 'Tipo']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"El DataFrame debe contener las columnas: {required_columns}")

    # Configurar el entorno de Jinja2 para cargar plantillas
    env = Environment(loader=FileSystemLoader('.'))  # Asegúrate de que la plantilla HTML está en el directorio actual
    template = env.get_template("carnet_template.html")  # Cargar la plantilla HTML

    # Configurar la ruta de wkhtmltopdf en la carpeta wkhtmltox
    path_wkhtmltopdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wkhtmltox', 'bin', 'wkhtmltopdf.exe')  # Cambia la extensión si no es Windows
    print("Ruta de wkhtmltopdf:", path_wkhtmltopdf)  # Imprimir la ruta para verificar
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)  # Configuración de PDFKit

    # Iterar a través de cada fila del DataFrame y generar un PDF
    for index, row in df.iterrows():
        pdf_filename = generate_pdf(row, template, config)  # Pasar la configuración a la función
        print(f"PDF generado: {pdf_filename}")  # Mensaje de confirmación de generación de PDF
