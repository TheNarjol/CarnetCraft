import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, Menu
from tkinter import ttk
from jinja2 import Environment, FileSystemLoader
import pdfkit
import os

class PDFGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Carnets PDF")
        
        # Crear una barra de menú
        self.menu_bar = Menu(root)
        self.root.config(menu=self.menu_bar)

        # Agregar un menú de archivo
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Abrir archivo Excel", command=self.load_file)
        self.menu_bar.add_cascade(label="Archivo", menu=file_menu)

        # Botón para seleccionar o deseleccionar todos
        self.select_all_button = tk.Button(root, text="Seleccionar/Deseleccionar Todos", command=self.toggle_select_all)
        self.select_all_button.pack(pady=5, anchor='w', padx=10)

        # Tabla para mostrar los datos
        self.tree = ttk.Treeview(root, columns=("Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "Tipo", "Previsualizar", "Generar"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.column("Previsualizar", width=100)  # Ajustar el ancho de la columna
        self.tree.column("Generar", width=100)  # Ajustar el ancho de la columna
        self.tree.pack(pady=10, padx=10, fill='both', expand=True)

        # Botón para generar PDFs
        self.generate_button = tk.Button(root, text="Generar PDFs", command=self.generate_pdfs)
        self.generate_button.pack(pady=5, anchor='w', padx=10)

        self.df = None  # DataFrame para almacenar los datos

        # Vincular el evento de clic en la tabla
        self.tree.bind("<ButtonRelease-1>", self.on_treeview_click)

        # Agregar un combobox para seleccionar el tipo de carnet
        self.tipo_carnet_var = tk.StringVar()
        self.tipo_carnet_combobox = ttk.Combobox(root, textvariable=self.tipo_carnet_var)
        self.tipo_carnet_combobox['values'] = ("Profesional", "Gerencial", "Administrativo")
        self.tipo_carnet_combobox.current(0)  # Establecer el valor predeterminado
        self.tipo_carnet_combobox.pack(pady=5, anchor='w', padx=10)

    def toggle_select_all(self):
        """Selecciona o deselecciona todos los carnets en el Treeview."""
        if len(self.tree.selection()) == len(self.tree.get_children()):
            for item in self.tree.get_children():
                self.tree.selection_remove(item)
        else:
            for item in self.tree.get_children():
                self.tree.selection_add(item)

    def preview_carnet(self, item):
        data_row = self.tree.item(item)['values']
        data_row_dict = dict(zip(self.tree["columns"], data_row))

        env = Environment(loader=FileSystemLoader('.'))
        try:
            template = env.get_template("carnet_template.html")
            html_out = template.render(data_row=data_row_dict)

            preview_window = tk.Toplevel(self.root)
            preview_window.title("Previsualización de Carnet")

            text_widget = tk.Text(preview_window, wrap='word')
            text_widget.insert('1.0', html_out)
            text_widget.config(state='disabled')
            text_widget.pack(expand=True, fill='both')

            close_button = tk.Button(preview_window, text="Cerrar", command=preview_window.destroy)
            close_button.pack(pady=10)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la plantilla: {str(e)}")

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            try:
                self.df = pd.read_excel(file_path)
                required_columns = ['Nombre', 'Apellidos', 'Cedula', 'Adscrito', 'Cargo']
                
                if not all(col in self.df.columns for col in required_columns):
                    raise ValueError(f"El DataFrame debe contener las columnas: {required_columns}")

                for i in self.tree.get_children():
                    self.tree.delete(i)

                for index, row in self.df.iterrows():
                    self.tree.insert("", "end", values=list(row) + ["Previsualizar", "Generar"])  # Agregar un valor placeholder
            except Exception as e:
                messagebox.showerror("Error ", str(e))

    def generate_carnet(self, item):
        data_row = self.tree.item(item)['values']
        data_row_dict = dict(zip(self.tree["columns"], data_row))

        env = Environment(loader=FileSystemLoader('.'))
        path_wkhtmltopdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wkhtmltox', 'bin', 'wkhtmltopdf.exe')
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        try:
            template = env.get_template("carnet_template.html")
            html_out = template.render(data_row=data_row_dict)

            pdf_file_path = f"{data_row_dict['Nombre']}_{data_row_dict['Apellidos']}_carnet.pdf"
            pdfkit.from_string(html_out, pdf_file_path, configuration=config)

            messagebox.showinfo("Éxito", f"Carnet generado: {pdf_file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el carnet: {str(e)}")

    def generate_pdfs(self):
        if self.df is None:
            messagebox.showwarning("Advertencia", "Por favor, carga un archivo Excel primero.")
            return

        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Por favor, selecciona al menos un carnet para generar PDFs.")
            return

        env = Environment(loader=FileSystemLoader('.'))
        path_wkhtmltopdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wkhtmltox', 'bin', 'wkhtmltopdf.exe')
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        for item in selected_items:
            data_row = self.tree.item(item)['values']
            tipo_carnet = self.tipo_carnet_var.get()  # Obtener el tipo de carnet del combobox

            # Seleccionar la plantilla según el tipo de carnet
            try:
                if tipo_carnet == "Profesional":
                    template = env.get_template("carnet_profesional_template.html")
                elif tipo_carnet == "Gerencial":
                    template = env.get_template("carnet_gerencial_template.html")
                elif tipo_carnet == "Administrativo":
                    template = env.get_template("carnet_administrativo_template.html")
                else:
                    messagebox.showwarning("Advertencia", "Tipo de carnet no válido.")
                    continue  # Salta a la siguiente iteración si el tipo de carnet no es válido

                pdf_filename = self.generate_pdf(dict(zip(self.tree["columns"], data_row)), template, config)
                print(f"PDF generado: {pdf_filename}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar el PDF para {tipo_carnet}: {str(e)}")

        messagebox.showinfo("Éxito", "Todos los PDFs seleccionados han sido generados.")

    def generate_pdf(self, data_row, template, config):
        html_out = template.render(data_row=data_row)
        pdf_filename = f"{data_row['Cedula']}_{self.tipo_carnet_var.get()}.pdf"  # Cambiar 'Tipo' por el valor del combobox

        pdfkit.from_string(html_out, pdf_filename, configuration=config, options={"enable-local-file-access": None})

        return pdf_filename

    def on_treeview_click(self, event):
        item = self.tree.selection()
        if item:
            clicked_item = item[0]
            column = self.tree.identify_column(event.x)
            column_index = int(column.replace("#", "")) - 1

            if column_index == len(self.tree["columns"]) - 2:
                self.preview_carnet(clicked_item) 

            elif column_index == len(self.tree["columns"]) - 1:
                self.generate_carnet(clicked_item)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFGeneratorApp(root)
    root.mainloop()