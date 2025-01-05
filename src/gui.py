import pandas as pd # type: ignore
import tkinter as tk
import os
import logging
import json
from tkinter import filedialog, messagebox, Menu
from tkinter import ttk
import traceback

# Asegúrate de tener la clase ImageGenerator implementada
from image_generator import ImageGenerator
from PIL import Image, ImageTk  # Asegúrate de tener Pillow instalado
from datetime import datetime

# Configure el logger
logging.basicConfig(
    filename='error_log.log',  # Nombre del archivo de log
    level=logging.ERROR,        # Nivel de log
    format='%(asctime)s - %(levelname)s - %(message)s'  # Formato del log
)


class ImageGeneratorApp:
    def __init__(self, root):
        """Inicializa la aplicación de generación de carnets de imagen."""
        self.root = root
        self.load_settings()  # Cargar configuraciones al iniciar
        self.root.title("Carnet Craft")
        
        # Crear una barra de menú
        self.menu_bar = Menu(root)
        self.root.config(menu=self.menu_bar)
        
        # Agregar un menú de archivo
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(
            label="Importar archivo Excel", command=self.load_file)
        self.menu_bar.add_cascade(label="Archivo", menu=file_menu)
        
        # Agregar un menú de editar
        edit_menu = Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Configuraciones", command=self.open_settings_window)
        self.menu_bar.add_cascade(label="Editar", menu=edit_menu)
        
        # Botón para seleccionar o deseleccionar todos
        self.select_all_button = tk.Button(
            root,
            text="Seleccionar Todos",
            command=self.toggle_select_all,
        )
        self.select_all_button.pack(pady=5, anchor="w", padx=10)
        # Tabla para mostrar los datos
        self.tree = ttk.Treeview(
            root,
            columns=("Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo"),
            show="headings",
        )
        # Configurar encabezados de la tabla
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(pady=10, padx=10, fill="both", expand=True)
        # Asociar el evento de doble clic con el método open_detail_window
        self.tree.bind("<Double-1>", self.open_detail_window)
        # Botón para generar imágenes
        self.generate_button = tk.Button(
            root, text="Generar Imágenes", command=self.generate_images)
        self.generate_button.pack(pady=5, anchor="se", padx=10)
        # Botón para crear una nueva entrada
        self.new_entry_button = tk.Button(
            root, text="+", command=self.open_new_entry_window
        )
        self.new_entry_button.pack(pady=5, anchor="w", padx=10)
        # DataFrame para almacenar los datos
        self.df = None
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
        # Establecer el valor predeterminado
        self.tipo_carnet_combobox.current(0)
        self.tipo_carnet_combobox.pack(pady=5, anchor="w", padx=10)
        # Instancia del generador de imágenes
        self.image_generator = ImageGenerator()

    def open_settings_window(self):
        """Abre la ventana de configuración."""
        SettingsWindow(self.root, self)

    def open_entry_window(self, title, item_values=None):
        """Abre una ventana para ingresar o editar los detalles de un trabajador."""
        EntryDetailWindow(self.root, self, title, item_values)

    def open_new_entry_window(self):
        """Abre una nueva ventana para ingresar los detalles de un nuevo trabajador."""
        self.open_entry_window("Nueva Entrada")

    def open_detail_window(self, event):
        """Abre una ventana para ver y editar los detalles de un trabajador seleccionado."""
        selected_item = self.tree.selection()
        if selected_item:
            item_values = self.tree.item(selected_item, 'values')
            self.open_entry_window("Editar Entrada", item_values)
    
    def save_new_entry(self, edit_vars, detail_window):
        self.save_entry(edit_vars, detail_window)

    def toggle_select_all(self):
        """Selecciona o deselecciona todos los carnets en el Treeview."""
        if len(self.tree.selection()) == len(self.tree.get_children()):
            for item in self.tree.get_children():
                self.tree.selection_remove(item)
        else:
            for item in self.tree.get_children():
                self.tree.selection_add(item)

    def load_file(self):
        """Carga un archivo y llena el Treeview con los datos."""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Archivos de Excel", "*.xlsx *.xlsm *.xls"),  # Excel
                ("Archivos de OpenDocument", "*.ods"),          # OpenDocument
                ("Archivos CSV", "*.csv"),                       # CSV
                ("Archivos TSV", "*.tsv"),                       # TSV
                # Todos los archivos
                ("Todos los Archivos", "*.*")
            ],
            title="Selecciona un archivo"
        )
        if file_path:
            try:
                # Determinar el tipo de archivo y cargarlo en un DataFrame
                if file_path.endswith(('.xlsx', '.xlsm', '.xls')):
                    self.df = pd.read_excel(file_path)
                elif file_path.endswith('.ods'):
                    self.df = pd.read_excel(file_path, engine='odf')
                elif file_path.endswith('.csv'):
                    self.df = pd.read_csv(file_path)
                elif file_path.endswith('.tsv'):
                    self.df = pd.read_csv(file_path, sep='\t')
                else:
                    raise ValueError("Formato de archivo no soportado.")
                required_columns = [
                    "Nombre",
                    "Apellidos",
                    "Cedula",
                ]
                # Verificar que las columnas requeridas estén presentes
                if not all(col in self.df.columns for col in required_columns):
                    raise ValueError(
                        f"El Data Frame debe contener las columnas: {
                            required_columns}"
                    )
                # Mostrar ventana de confirmación
                self.show_confirmation_window()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def load_settings(self):
        """Carga las configuraciones desde un archivo JSON."""
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.root.title(settings.get("app_title", "Carnet Craft"))
                self.root.config(bg=settings.get("bg_color", "white"))
        except FileNotFoundError:
            # Si el archivo no existe, se utilizarán los valores predeterminados
            self.root.title("Carnet Craft")
            self.root.config(bg="white")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Error al cargar las configuraciones.")

    def show_confirmation_window(self):
        """Muestra una ventana de confirmación con los datos cargados."""
        confirmation_window = tk.Toplevel(self.root)
        confirmation_window.title("Confirmar Carga de Datos")
        # Crear un Treeview para mostrar los datos
        confirmation_tree = ttk.Treeview(confirmation_window, columns=(
            "Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo"), show="headings")
        for col in confirmation_tree["columns"]:
            confirmation_tree.heading(col, text=col)
        confirmation_tree.pack(pady=10, padx=10, fill="both", expand=True)
        # Insertar los datos en el Treeview de confirmación
        for index, row in self.df.iterrows():
            values = [
                row.get("Nombre", ""),
                row.get("Apellidos", ""),
                row.get("Cedula", ""),
                row.get("Adscrito", ""),
                row.get("Cargo", ""),
            ]
            confirmation_tree.insert("", "end", values=values)
        # Botón para cancelar
        cancel_button = tk.Button(
            confirmation_window, text="Cancelar", command=confirmation_window.destroy)
        cancel_button.pack(pady=5, anchor="w", padx=10)
        # Botón para aceptar y agregar los datos al Treeview principal
        accept_button = tk.Button(confirmation_window, text="Aceptar",
                                    command=lambda: self.accept_data(confirmation_window))
        accept_button.pack(pady=5, anchor="w", padx=10)

    def accept_data(self, confirmation_window):
        """Inserta los datos en el Treeview principal y cierra la ventana de confirmación."""
        for index, row in self.df.iterrows():
            values = [
                row.get("Nombre", ""),
                row.get("Apellidos", ""),
                row.get("Cedula", ""),
                row.get("Adscrito", ""),
                row.get("Cargo", ""),
                ""  # Campo vacío para la ruta de la imagen
            ]
            self.tree.insert("", "end", values=values)
        confirmation_window.destroy()  # Cerrar la ventana de confirmación

    def generate_images(self):
        """Genera imágenes para todos los carnets seleccionados en el Treeview."""
        # Verificar si hay al menos una entrada en el Treeview
        if len(self.tree.get_children()) == 0:
            messagebox.showwarning(
                "Advertencia", "No hay entradas. Por favor, añade al menos una entrada."
            )
            return

        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "Advertencia", "Por favor, selecciona al menos un carnet para generar imágenes."
            )
            return

        # Pedir al usuario que seleccione una ubicación para guardar los archivos
        output_directory = filedialog.askdirectory(title="Selecciona la ubicación para guardar los carnets")
        if not output_directory:
            messagebox.showwarning("Advertencia", "No se seleccionó ninguna ubicación.")
            return

        # Crear la carpeta con la fecha actual
        today = datetime.now().strftime("%Y_%m_%d")
        folder_name = f"carnets_{today}"
        full_path = os.path.join(output_directory, folder_name)

        # Crear la carpeta si no existe
        try:
            os.makedirs(full_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la carpeta: {str(e)}")
            return

        total_generados = 0
        total_errores = 0
        errores = []

        for item in selected_items:
            data_row = self.tree.item(item)["values"]
            tipo_carnet = self.tipo_carnet_var.get()
            ruta_imagen = data_row[5]

            # Comprobar que los campos obligatorios no estén vacíos
            nombre = data_row[0]
            apellidos = data_row[1]
            cedula = data_row[2]
            if not nombre or not apellidos or not cedula:
                messagebox.showwarning(
                    "Advertencia",
                    f"Faltan datos para el carnet: Nombre: {nombre}, Apellidos: {apellidos}, Cédula: {cedula}"
                )
                total_errores += 1
                continue  # Saltar a la siguiente iteración

            # Comprobar si la imagen existe
            if not os.path.exists(ruta_imagen):
                messagebox.showwarning(
                    "Advertencia",
                    f"Imagen no encontrada para {nombre} {apellidos} (Cédula: {cedula})"
                )
                total_errores += 1
                continue  # Saltar a la siguiente iteración

            try:
                # Generar la imagen y guardarla en la nueva carpeta
                image_filename = self.image_generator.generate_image(dict(zip(self.tree["columns"], data_row)), tipo_carnet, ruta_imagen)
                # Mover la imagen generada a la carpeta
                new_image_path = os.path.join(full_path, os.path.basename(image_filename))
                os.rename(image_filename, new_image_path)
                print(f"Imagen generada: {new_image_path}")
                total_generados += 1  # Incrementar contador de generados
            except FileNotFoundError as fnf_error:
                total_errores += 1
                errores.append(f"Archivo no encontrado: {str(fnf_error)}")
                logging.error(f"Archivo no encontrado: {str(fnf_error)} - {nombre} {apellidos} (Cédula: {cedula})")
            except PermissionError as perm_error:
                total_errores += 1
                errores.append(f"Permiso denegado al acceder a: {str(perm_error)}")
                logging.error(f"Permiso denegado: {str(perm_error)} - {nombre} {apellidos} (Cédula: {cedula})")
            except Exception as e:
                total_errores += 1
                error_message = f"Error al generar imagen para {nombre} {apellidos} (Cédula: {cedula}): {str(e)}"
                error_details = traceback.format_exc()  # Captura la traza del error
                errores.append(f"{error_message}\nDetalles del error:\n{error_details}")
                logging.error(f"No se pudo generar la imagen para {tipo_carnet}: {str(e)} - {nombre} {apellidos} (Cédula: {cedula})\nDetalles del error:\n{error_details}")
                            
        # Mensaje final con el resumen de la operación
        if total_errores > 0:
            error_message = "\n".join(errores)
            messagebox.showerror(
                "Errores en la generación",
                f"Se generaron {total_generados} carnets con éxito.\n"
                f"Se encontraron errores en {total_errores} carnets:\n{error_message}"
                )
        else:
            messagebox.showinfo(
                "Éxito", f"Todas las imágenes seleccionadas han sido generadas. Total: {total_generados}"
            )

    def is_valid_cedula(self, cedula):
        """Valida que la cédula contenga solo números y tenga 7 u 8 dígitos."""
        return cedula.isdigit() and len(cedula) in (7, 8)


class SettingsWindow:
    def __init__(self, root, app):
        """Inicializa la ventana de configuración."""
        self.root = root
        self.app = app
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Configuraciones")

        # Cargar configuraciones actuales
        self.app_title_var = tk.StringVar(value=self.app.root.title())
        self.bg_color_var = tk.StringVar(value=self.app.root.cget("bg"))

        # Crear la interfaz de usuario
        self.create_ui()

    def create_ui(self):
        """Crea la interfaz de usuario para la ventana de configuración."""
        # Ejemplo de configuración: Cambiar el título de la aplicación
        tk.Label(self.settings_window, text="Título de la Aplicación:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        tk.Entry(self.settings_window, textvariable=self.app_title_var).grid(row=0, column=1, padx=5, pady=5)

        # Ejemplo de configuración: Cambiar el color de fondo
        tk.Label(self.settings_window, text="Color de Fondo:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        tk.Entry(self.settings_window, textvariable=self.bg_color_var).grid(row=1, column=1, padx=5, pady=5)

        # Botón para guardar configuraciones
        tk.Button(self.settings_window, text="Guardar", command=self.save_settings).grid(row=2, column=0, columnspan=2, pady=10)

        # Botón para cancelar
        tk.Button(self.settings_window, text="Cancelar", command=self.settings_window.destroy).grid(row=3, column=0, columnspan=2, pady=5)

    def save_settings(self):
        """Guarda las configuraciones en un archivo JSON."""
        new_title = self.app_title_var.get()
        new_bg_color = self.bg_color_var.get()

        # Aplicar configuraciones
        self.app.root.title(new_title)
        self.app.root.config(bg=new_bg_color)

        # Guardar configuraciones en el archivo
        settings = {
            "app_title": new_title,
            "bg_color": new_bg_color
        }
        with open('settings.json', 'w') as f:
            json.dump(settings, f)

        self.settings_window.destroy()  # Cerrar la ventana


class EntryDetailWindow:
    def __init__(self, root, app, title, item_values=None):
        """Inicializa la ventana de entrada/detalle."""
        self.root = root
        self.app = app
        self.title = title
        self.item_values = item_values
        self.detail_window = tk.Toplevel(self.root)
        self.detail_window.title(title)
        self.edit_vars = [tk.StringVar(value=value) for value in (item_values or [""] * 6)]
        self.image_display = None
        self.create_ui()

    def create_ui(self):
        """Crea la interfaz de usuario para la ventana de entrada/detalle."""
        labels = ["Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "Ruta Imagen"]
        for i, label in enumerate(labels):
            tk.Label(self.detail_window, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            tk.Entry(self.detail_window, textvariable=self.edit_vars[i]).grid(row=i, column=1, padx=5, pady=5)

        # Label para mostrar la imagen
        self.image_display = tk.Label(self.detail_window, bd=2, relief="sunken")
        self.image_display.grid(row=len(labels), column=1, columnspan=2, pady=10)

        # Botón para seleccionar la imagen
        tk.Button(self.detail_window, text="Seleccionar Imagen", command=self.select_image).grid(row=len(labels), column=0, pady=5)

        # Botón para guardar nueva entrada o cambios
        action = "Guardar Nueva Entrada" if self.item_values is None else "Guardar Cambios"
        save_command = self.save_new_entry if self.item_values is None else lambda: self.save_changes(self.edit_vars, self.app.tree.selection()[0], self.detail_window)
        tk.Button(self.detail_window, text=action, command=save_command).grid(row=len(labels) + 2, column=0, columnspan=2, pady=5)

        # Cargar imagen si se está editando
        if self.item_values:
            self.load_image(self.item_values[5])

    def select_image(self):
        """Selecciona una imagen para el carnet."""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.edit_vars[5].set(file_path)
            img = Image.open(file_path)
            img.thumbnail((100, 100))
            img_tk = ImageTk.PhotoImage(img)
            self.image_display.config(image=img_tk)
            self.image_display.image = img_tk

    def load_image(self, img_path):
        """Carga y muestra la imagen en el label."""
        if os.path.isfile(img_path):
            img = Image.open(img_path)
            img.thumbnail((100, 100))
            img_tk = ImageTk.PhotoImage(img)
            self.image_display.config(image=img_tk)
            self.image_display.image = img_tk

    def save_new_entry(self):
        """Guarda una nueva entrada en el Treeview."""
        self.app.save_new_entry(self.edit_vars, self.detail_window)

    def save_changes(self, edit_vars, item_id, detail_window):
        """Guarda los cambios en una entrada existente en el Treeview."""
        self.app.save_changes(edit_vars, item_id, detail_window)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()
