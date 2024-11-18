"""
Generador de Carnets PDF a partir de datos en un archivo Excel.
Desarrollado por theNarjol.

Este script permite al usuario seleccionar un archivo Excel que contenga datos
de personas y generar carnets en formato PDF utilizando una plantilla HTML.
"""

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from jinja2 import Environment, FileSystemLoader
import pdfkit
import os

class PDFGeneratorApp:
    def __init__(self, root):
        """
        Inicializa la aplicación de generación de PDFs.

        Args:
            root (Tk): La ventana principal de la aplicación.
        """
        self.root = root
        self.root.title("Generador de Carnets PDF")
        
        # Botón para seleccionar archivo
        self.select_button = tk.Button(root, text="Seleccionar archivo Excel", command=self.load_file)
        self.select_button.pack(pady=10)

        # Botón para seleccionar o deseleccionar todos
        self.select_all_button = tk.Button(root, text="Seleccionar/Deseleccionar Todos", command=self.toggle_select_all)
        self.select_all_button.pack(pady=10)


        # Tabla para mostrar los datos
        self.tree = ttk.Treeview(root, columns=("Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "Tipo", "Previsualizar", "Generar"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(pady=10)


        # Botón para generar PDFs
        self.generate_button = tk.Button(root, text="Generar PDFs", command=self.generate_pdfs)
        self.generate_button.pack(pady=10)

        self.df = None  # DataFrame para almacenar los datos

        # Botón para previsualizar el carnet
        self.preview_button = tk.Button(root, text="Previsualizar Carnet", command=self.preview_carnet)
        self.preview_button.pack(pady=10)

        # Vincular el evento de clic en la tabla
        self.tree.bind("<ButtonRelease-1>", self.on_treeview_click)

    
    
    def toggle_select_all(self):
        """Selecciona o deselecciona todos los carnets en el Treeview."""
        if len(self.tree.selection()) == len(self.tree.get_children()):
            # Si todos están seleccionados, deselecciona todos
            for item in self.tree.get_children():
                self.tree.selection_remove(item)
        else:
            # Si no todos están seleccionados, selecciona todos
            for item in self.tree.get_children():
                self.tree.selection_add(item)

    def preview_carnet(self, item):
        """
        Previsualiza el carnet en una ventana emergente.

        Toma la fila seleccionada en la tabla y genera un HTML para mostrar
        el carnet en una nueva ventana.
        """
        data_row = self.tree.item(item)['values']
        data_row_dict = dict(zip(self.tree["columns"], data_row))

        # Configurar el entorno de Jinja2 para cargar plantillas
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("carnet_template.html")

        # Renderizar el HTML con los datos de la fila
        html_out = template.render(data_row=data_row_dict)

        # Crear una nueva ventana para la previsualización
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Previsualización de Carnet")

        # Usar un Text widget para mostrar el HTML
        text_widget = tk.Text(preview_window, wrap='word')
        text_widget.insert('1.0', html_out)
        text_widget.config(state='disabled')  # Hacer el Text widget de solo lectura
        text_widget.pack(expand=True, fill='both')

        # Botón para cerrar la ventana de previsualización
        close_button = tk.Button(preview_window, text="Cerrar", command=preview_window.destroy)
        close_button.pack(pady=10)


    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            try:
                self.df = pd.read_excel(file_path)
                required_columns = ['Nombre', 'Apellidos', 'Cedula', 'Adscrito', 'Cargo', 'Tipo']
                
                if not all(col in self.df.columns for col in required_columns):
                    raise ValueError(f"El DataFrame debe contener las columnas: {required_columns}")

                for i in self.tree.get_children():
                    self.tree.delete(i)

                # Insertar datos en la tabla
                for index, row in self.df.iterrows():
                    self.tree.insert("", "end", values=list(row) + ["Previsualizar", "Generar Carnet"])

            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def generate_pdfs(self):
        """
        Genera archivos PDF a partir de los datos cargados en el DataFrame.

        Verifica que se haya cargado un archivo Excel y genera un PDF para
        cada fila de datos utilizando la plantilla HTML.
        """
        if self.df is None:
            messagebox.showwarning("Advertencia", "Por favor, carga un archivo Excel primero.")
            return

        # Configurar el entorno de Jinja2 para cargar plantillas
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("carnet_template.html")

        # Configurar la ruta de wkhtmltopdf
        path_wkhtmltopdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wkhtmltox', 'bin', 'wkhtmltopdf.exe')
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        # Generar PDFs
        for index, row in self.df.iterrows():
            pdf_filename = self.generate_pdf(row, template, config)
            print(f"PDF generado: {pdf_filename}")

        # Mensaje de éxito al finalizar la generación de PDFs
        messagebox.showinfo("Éxito", "Todos los PDFs han sido generados.")


    def generate_carnet(self, item):
        """
        Genera el carnet en formato PDF a partir de la fila seleccionada.

        Toma la fila seleccionada en la tabla y genera un PDF utilizando
        los datos de la fila.
        """
        data_row = self.tree.item(item)['values']
        data_row_dict = dict(zip(self.tree["columns"], data_row))

        # Configurar el entorno de Jinja2 para cargar plantillas
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("carnet_template.html")

        # Configurar la ruta de wkhtmltopdf
        path_wkhtmltopdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wkhtmltox', 'bin', 'wkhtmltopdf.exe')
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        # Renderizar el HTML con los datos de la fila
        html_out = template.render(data_row=data_row_dict)

        # Generar el PDF
        pdf_file_path = f"{data_row_dict['Nombre']}_{data_row_dict['Apellidos']}_carnet.pdf"
        pdfkit.from_string(html_out, pdf_file_path, configuration=config)

        messagebox.showinfo("Éxito", f"Carnet generado: {pdf_file_path}")

    def generate_pdf(self, data_row, template, config):
        """
        Genera un archivo PDF a partir de una fila de datos y una plantilla HTML.

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

    def on_treeview_click(self, event):
        """Maneja el clic en la tabla para realizar acciones específicas."""
        item = self.tree.selection()
        if item:
            clicked_item = item[0]
            column = self.tree.identify_column(event.x)
            column_index = int(column.replace("#", "")) - 1  # Convertir a índice de columna

            if column_index == len(self.tree["columns"]) - 2:  # Columna "Acción Previsualizar"
                self.preview_carnet(clicked_item)
            elif column_index == len(self.tree["columns"]) - 1:  # Columna "Acción Generar"
                self.generate_carnet(clicked_item)


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFGeneratorApp(root)
    root.mainloop()