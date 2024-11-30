import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, Menu
from tkinter import ttk
from jinja2 import Environment, FileSystemLoader
import pdfkit
import os
import platform

class PDFGeneratorApp:
    def __init__(self, root):
        """Inicializa la aplicación de generación de carnets PDF."""
        self.root = root
        self.root.title("Generador de Carnets PDF")

        # Crear una barra de menú
        self.menu_bar = Menu(root)
        self.root.config(menu=self.menu_bar)
        # Agregar un menú de archivo
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(
            label="Abrir archivo Excel", command=self.load_file
        )
        self.menu_bar.add_cascade(label="Archivo", menu=file_menu)
        # Botón para seleccionar o deseleccionar todos
        self.select_all_button = tk.Button(
            root,
            text="Seleccionar/Deseleccionar Todos",
            command=self.toggle_select_all,
        )
        self.select_all_button.pack(pady=5, anchor="w", padx=10)
        # Tabla para mostrar los datos
        self.tree = ttk.Treeview(
            root,
            columns=("Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo"),
            show="headings",
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(pady=10, padx=10, fill="both", expand=True)
        # Botón para generar PDFs
        self.generate_button = tk.Button(
            root, text="Generar PDFs", command=self.generate_pdfs
        )
        self.generate_button.pack(pady=5, anchor="w", padx=10)
        self.df = None  # DataFrame para almacenar los datos
        # Agregar un combobox para seleccionar el tipo de carnet
        self.tipo_carnet_var = tk.StringVar()
        self.tipo_carnet_combobox = ttk.Combobox(
            root, textvariable=self.tipo_carnet_var
        )
        self.tipo_carnet_combobox["values"] = (
            "Profesional",
            "Gerencial",
            "Administrativo",
        )
        self.tipo_carnet_combobox.current(
            0
        )  # Establecer el valor predeterminado
        self.tipo_carnet_combobox.pack(pady=5, anchor="w", padx=10)

    def toggle_select_all(self):
        """Selecciona o deselecciona todos los carnets en el Treeview."""
        if len(self.tree.selection()) == len(self.tree.get_children()):
            for item in self.tree.get_children():
                self.tree.selection_remove(item)
        else:
            for item in self.tree.get_children():
                self.tree.selection_add(item)

    def load_file(self):
        """Carga un archivo Excel y llena el Treeview con los datos."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx;*.xls")]
        )
        if file_path:
            try:
                self.df = pd.read_excel(file_path)
                required_columns = [
                    "Nombre",
                    "Apellidos",
                    "Cedula",
                    "Adscrito",
                    "Cargo",
                ]

                if not all(col in self.df.columns for col in required_columns):
                    raise ValueError(
                        f"El DataFrame debe contener las columnas: {required_columns}"
                    )
                # Limpiar el Treeview antes de cargar nuevos datos
                for i in self.tree.get_children():
                    self.tree.delete(i)
                # Insertar los datos en el Treeview
                for index, row in self.df.iterrows():
                    self.tree.insert(
                        "", "end", values=list(row)
                    )  # Agregar solo los valores relevantes
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def generate_pdfs(self):
        """Genera PDFs para todos los carnets seleccionados en el Treeview."""
        if self.df is None:
            messagebox.showwarning(
                "Advertencia", "Por favor, carga un archivo Excel primero."
            )
            return
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "Advertencia",
                "Por favor, selecciona al menos un carnet para generar PDFs.",
            )
            return
        env = Environment(loader=FileSystemLoader("."))
        
        # # Determinar la ruta de wkhtmltopdf según el sistema operativo
        if platform.system() == "Windows":
            path_wkhtmltopdf = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "wkhtmltox",
                "bin",
                "wkhtmltopdf.exe",
            )
        else:  # Asumir que es Linux
            path_wkhtmltopdf = "/usr/local/bin/wkhtmltopdf"  # Asegúrate de que wkhtmltopdf esté en el PATH

        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        for item in selected_items:
            data_row = self.tree.item(item)["values"]
            tipo_carnet = (
                self.tipo_carnet_var.get()
            )  # Obtener el tipo de carnet del combobox
            # Seleccionar la plantilla según el tipo de carnet
            try:
                if tipo_carnet == "Profesional":
                    template = env.get_template(
                        "carnet_profesional_template.html"
                    )
                elif tipo_carnet == "Gerencial":
                    template = env.get_template(
                        "carnet_gerencial_template.html"
                    )
                elif tipo_carnet == "Administrativo":
                    template = env.get_template(
                        "carnet_administrativo_template.html"
                    )
                else:
                    messagebox.showwarning(
                        "Advertencia", "Tipo de carnet no válido."
                    )
                    continue  # Salta a la siguiente iteración si el tipo de carnet no es válido
                pdf_filename = self.generate_pdf(
                    dict(zip(self.tree["columns"], data_row)), template, config
                )
                print(f"PDF generado: {pdf_filename}")
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"No se pudo generar el PDF para {tipo_carnet}: {str(e)}",
                )
        messagebox.showinfo(
            "Éxito", "Todos los PDFs seleccionados han sido generados."
        )

    def generate_pdf(self, data_row, template, config):
        """Genera un PDF a partir de los datos y la plantilla proporcionada."""
        html_out = template.render(data_row=data_row)
        pdf_filename = f"{data_row['Cedula']}_{self.tipo_carnet_var.get()}.pdf"  # Cambiar 'Tipo' por el valor del combobox
        pdfkit.from_string(
            html_out,
            pdf_filename,
            configuration=config,
            options={"enable-local-file-access": None},
        )
        return pdf_filename


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFGeneratorApp(root)
    root.mainloop()