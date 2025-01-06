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
        self.root.title("Carnet Craft")
        
        # Iniciar la ventana maximizada
        self.maximize_window()  # Método para manejar la maximización
        
        # Crear una barra de menú
        self.create_menu_bar()
        
        # Crear el Frame principal para el Treeview y el Sidebar
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Crear el Treeview y los botones de selección
        self.create_treeview_and_buttons()
        
        # Crear el Sidebar
        self.create_sidebar()
        
        # DataFrame para almacenar los datos
        self.df = None
        self.oficinas = [("Oficina 1", "OF1"), ("Oficina 2", "OF2")]


        # Instancia del generador de imágenes
        self.image_generator = ImageGenerator()

        # Configurar tags para colores
        self.tree.tag_configure('missing_data', background='yellow')
        self.tree.tag_configure('error_data', background='red')
        
        # Cargar una imagen en blanco de 100x100 por defecto
        self.load_default_image()

    def maximize_window(self):
        """
        Intenta maximizar la ventana usando la solución más compatible.
        Si falla, recurre a ajustar manualmente el tamaño de la ventana.
        """
        try:
            # Intentar usar wm_attributes (solución más compatible)
            self.root.attributes('-zoomed', True)
        except Exception:
            # Si falla, ajustar manualmente el tamaño de la ventana
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")

    def create_menu_bar(self):
        """Crea la barra de menú de la aplicación."""
        self.menu_bar = Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Agregar un menú de archivo
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(
            label="Importar archivo Excel", command=self.load_file)
        self.menu_bar.add_cascade(label="Archivo", menu=file_menu)
        
        # Agregar un menú de editar
        edit_menu = Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Configuraciones", command=self.open_settings_window)
        edit_menu.add_command(label="Oficinas", command=self.open_custom_entry_window)
        self.menu_bar.add_cascade(label="Editar", menu=edit_menu)

    def create_treeview_and_buttons(self):
        """Crea el Treeview y los botones de selección."""
        # Botón para seleccionar o deseleccionar todos
        self.select_all_button = tk.Button(
            self.root,
            text="Seleccionar Todos",
            command=self.toggle_select_all,
        )
        self.select_all_button.pack(pady=5, anchor="w", padx=10)
        
        # Tabla para mostrar los datos
        self.tree = ttk.Treeview(
            self.main_frame,
            columns=("Nombre", "Apellidos", "Cedula", "Adscrito"),
            show="headings"
        )
        
        # Definir los nombres de las columnas
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Apellidos", text="Apellidos")
        self.tree.heading("Cedula", text="Cédula")
        self.tree.heading("Adscrito", text="Adscrito")

        
        # Configurar encabezados de la tabla
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Asociar el evento de doble clic con el método open_detail_window
        self.tree.bind("<Double-1>", self.open_detail_window)
        
        # Botón para generar imágenes
        self.generate_button = tk.Button(
            self.root, text="Generar Imágenes", command=self.generate_images)
        self.generate_button.pack(pady=5, anchor="se", padx=10)

        # Botón para crear una nueva entrada
        self.new_entry_button = tk.Button(
            self.root, text="+", command=self.open_new_entry_window
        )
        self.new_entry_button.pack(pady=5, anchor="w", padx=10)

    def create_sidebar(self):
        """Crea el sidebar con los labels y el botón de editar."""
        # Crear el sidebar
        self.sidebar = tk.Frame(self.main_frame, width=200, bg="lightgray")
        self.sidebar.pack(side="right", fill="y", padx=10, pady=10)
        self.sidebar.pack_propagate(False)  # Evitar que el sidebar se expanda automáticamente

        # Label para mostrar el estado de la selección (ninguna, una o múltiple)
        self.selection_status_label = tk.Label(
            self.sidebar, text="Ninguna selección", bg="lightgray", font=("Arial", 12, "bold")
        )
        self.selection_status_label.pack(pady=10)

        # Labels para los detalles de la fila seleccionada
        self.sidebar_labels = {
            "Nombre": tk.Label(self.sidebar, text="Nombre:", bg="lightgray"),
            "Apellidos": tk.Label(self.sidebar, text="Apellidos:", bg="lightgray"),
            "Cedula": tk.Label(self.sidebar, text="Cédula:", bg="lightgray"),
            "Adscrito": tk.Label(self.sidebar, text="Adscrito:", bg="lightgray"),
            "Cargo": tk.Label(self.sidebar, text="Cargo:", bg="lightgray"),
            "Tipo": tk.Label(self.sidebar, text="Tipo:", bg="lightgray"),
        }

        # Colocar los labels en el sidebar
        for label in self.sidebar_labels.values():
            label.pack(pady=5)
            label.pack_forget()  # Ocultar los labels por defecto


        # Label para mostrar la miniatura de la imagen
        self.image_display = tk.Label(self.sidebar, bd=2, relief="sunken", bg="white")
        self.image_display.pack(pady=10)
        self.image_display.pack_forget()  # Ocultar la imagen por defecto

        # Botón para editar
        self.edit_button = tk.Button(
            self.sidebar, text="Editar", command=self.open_edit_window, state="disabled"
        )
        self.edit_button.pack(side="bottom", fill="x", pady=5)  # Pegar al borde inferior

        # Asociar el evento de selección con el método update_sidebar
        self.tree.bind("<<TreeviewSelect>>", self.update_sidebar)

    def update_sidebar(self, event=None):
        """Actualiza el sidebar según la selección en el Treeview."""
        selected_items = self.tree.selection()  # Obtener las filas seleccionadas

        if len(selected_items) == 0:
            # Ninguna fila seleccionada
            self.selection_status_label.config(text="Ninguna selección")
            self.selection_status_label.pack(pady=10)  # Mostrar el label
            for label in self.sidebar_labels.values():
                label.pack_forget()  # Ocultar los labels de detalles
            self.clear_image_display()  # Limpiar la imagen
            self.edit_button.config(state="disabled")  # Desactivar el botón "Editar"
        elif len(selected_items) == 1:
            # Una fila seleccionada
            self.selection_status_label.pack_forget()  # Ocultar el label de estado
            for label in self.sidebar_labels.values():
                label.pack(pady=5)  # Mostrar los labels de detalles

            # Mostrar los detalles de la fila seleccionada
            item_values = self.tree.item(selected_items[0], 'values')
            self.sidebar_labels["Nombre"].config(text=f"Nombre: {item_values[0 ]}")
            self.sidebar_labels["Apellidos"].config(text=f"Apellidos: {item_values[1]}")
            self.sidebar_labels["Cedula"].config(text=f"Cédula: {item_values[2]}")
            self.sidebar_labels["Adscrito"].config(text=f"Adscrito: {item_values[3]}")
            self.sidebar_labels["Cargo"].config(text=f"Cargo: {item_values[4]}")
            self.sidebar_labels["Tipo"].config(text=f"Tipo: {item_values[6]}")
            

            self.image_display.pack()  # Mostrar la imagen
            if item_values[5]:  # Verificar si el campo no está vacío
                self.load_image_thumbnail(item_values[5])  # Método para actualizar la imagen
            else:
                self.clear_image_display()
            self.edit_button.config(state="normal")  # Activar el botón "Editar"
            self.edit_button.pack(side="bottom", fill="x", pady=5)  # Asegurarse de que el botón esté visible

        else:
            # Selección múltiple
            self.selection_status_label.config(text="Selección múltiple")
            self.selection_status_label.pack(pady=10)  # Mostrar el label
            for label in self.sidebar_labels.values():
                label.pack_forget()  # Ocultar los labels de detalles
            self.clear_image_display()  # Limpiar la imagen
            self.edit_button.config(state="disabled")  # Desactivar el botón "Editar"

    def load_image_thumbnail(self, img_path):
        """Carga y muestra la miniatura de la imagen en el sidebar."""
        
        try:
            img = Image.open(img_path)
            img.thumbnail((100, 100))  # Redimensionar la imagen
            img_tk = ImageTk.PhotoImage(img)
            self.image_display.config(image=img_tk)
            self.image_display.image = img_tk  # Mantener una referencia para evitar que se elimine
        except Exception as e:
            # Mostrar un mensaje de error si no se puede cargar la imagen
            messagebox.showerror("Error", f"No se pudo cargar la imagen: {str(e)}")
            self.clear_image_display()

    def clear_image_display(self):
        """Limpia la imagen mostrada en el sidebar y carga una imagen en blanco por defecto."""
        self.image_display.config(image=None)
        self.image_display.image = None  # Eliminar la referencia a la imagen anterior

        # Cargar la imagen en blanco por defecto
        self.load_default_image()

    def load_default_image(self):
        """Carga una imagen en blanco de 100x100 por defecto."""
        img = Image.new('RGB', (100, 100), color=(255, 255, 255))  # Crear una imagen en blanco
        img_tk = ImageTk.PhotoImage(img)
        self.image_display.config(image=img_tk)
        self.image_display.image = img_tk  # Mantener una referencia para evitar que se elimine
        
    def open_settings_window(self):
        """Abre la ventana de configuración."""
        SettingsController(self.root)

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
        self.update_row_colors()  # Actualizar colores después de cargar los datos

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
                "",  # Campo vacío para la ruta de la imagen
                "" # Campo vacío para tipo
                
            ]
            self.tree.insert("", "end", values=values)
        confirmation_window.destroy()  # Cerrar la ventana de confirmación
        self.update_row_colors()  # Actualizar colores después de cargar los datos

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
            # Reemplazar la abreviatura por el nombre completo de la oficina
            oficina_abreviatura = data_row[3]
            oficina_nombre = next((oficina[0] for oficina in self.oficinas if oficina[1] == oficina_abreviatura), None)
            if oficina_nombre:
                data_row = list(data_row)  # Convertir a lista para poder modificar
                data_row[3] = oficina_nombre  # Reemplazar la abreviatura por el nombre completo
                data_row = tuple(data_row)  # Convertir de vuelta a tupla

            # Comprobar que los campos obligatorios no estén vacíos
            ruta_imagen = data_row[5]
            tipo_carnet = data_row[6]
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
                column = ["Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "RutaImagen", "TipoCarnet"]
                data = dict(zip(column, data_row))
                image_filename = self.image_generator.generate_image(data)
                # Mover la imagen generada a la carpeta
                new_image_path = os.path.join(full_path, os.path.basename(image_filename))
                os.rename(image_filename, new_image_path)
                print(f"Imagen generada: {new_image_path}")
                total_generados += 1  # Incrementar contador de generados
            
            except FileNotFoundError as fnf_error:
                total_errores += 1
                errores.append(f"Archivo no encontrado: {str(fnf_error)}")
                print(str(e))
                logging.error(f"Archivo no encontrado: {str(fnf_error)} - {nombre} {apellidos} (Cédula: {cedula})")
            except PermissionError as perm_error:
                total_errores += 1
                errores.append(f"Permiso denegado al acceder a: {str(perm_error)}")
                print(str(e))
                logging.error(f"Permiso denegado: {str(perm_error)} - {nombre} {apellidos} (Cédula: {cedula})")
            except Exception as e:
                total_errores += 1
                error_message = f"Error al generar imagen para {nombre} {apellidos} (Cédula: {cedula}):"
                print(str(e))
                error_details = traceback.format_exc()  # Captura la traza del error
                errores.append(f"{error_message}\nDetalles del error:\n{str(e)}")
                print(error_details)
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

    def validate_row(self, values):
        """
        Valida si una fila tiene datos faltantes o errores.
        Devuelve el tag correspondiente ('missing_data', 'error_data') o None si no hay problemas.
        """
        # Extraer valores
        nombre = values[0]
        apellidos = values[1]
        cedula = values[2]
        ruta_imagen = values[5]  # Índice 5 corresponde a la ruta de la imagen

        # Verificar datos faltantes
        if not nombre or not apellidos or not cedula or not ruta_imagen:
            return 'missing_data'

        # Verificar si la imagen existe
        if not os.path.isfile(ruta_imagen):
            return 'missing_data'

        # Verificar errores en la cédula
        if not self.is_valid_cedula(cedula):
            return 'error_data'

        return None  # No hay errores ni datos faltantes
    
    def update_row_colors(self):
        """Actualiza los colores de las filas según los datos."""
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            tag = self.validate_row(values)
            self.tree.item(item, tags=(tag,))

    def open_edit_window(self):
        """Abre la ventana de edición para la fila seleccionada."""
        selected_item = self.tree.selection()  # Obtener la fila seleccionada
        if selected_item:  # Verificar si hay una fila seleccionada
            item_values = self.tree.item(selected_item, 'values')  # Obtener los valores de la fila
            # Abrir la ventana de edición con los valores actuales
            self.open_entry_window("Editar Entrada", item_values)

    def open_custom_entry_window(self):
        """Abre la ventana personalizada para agregar o editar oficinas."""
        ofiEntryWindow(self.root, self, "Gestión de oficinas")


class SettingsModel:
    def __init__(self):
        self.settings = {
            "mysql_user": "",
            "mysql_pass": "",
            "mysql_host": "",
            "mysql_port": "3306",
        }

    def load_settings(self):
        """Carga las configuraciones desde el archivo settings.json."""
        try:
            with open('settings.json', 'r') as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            # Si el archivo no existe, se utilizarán los valores predeterminados
            pass
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Error al cargar las configuraciones.")

    def save_settings(self, settings):
        """Guarda las configuraciones en el archivo settings.json."""
        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar las configuraciones: {str(e)}")
            return False


class SettingsView:
    def __init__(self, root, controller):
        """Inicializa la vista de configuración."""
        self.settings_window = tk.Toplevel(root)
        self.settings_window.title("Configuraciones")
        self.controller = controller

        # Variables para los campos de entrada
        self.app_title_var = tk.StringVar()
        self.bg_color_var = tk.StringVar()
        self.mysql_user_var = tk.StringVar()
        self.mysql_pass_var = tk.StringVar()
        self.mysql_host_var = tk.StringVar()
        self.mysql_port_var = tk.StringVar(value="3306")

        # Crear la interfaz de usuario
        self.create_ui()

    def create_ui(self):
        """Crea la interfaz de usuario para la ventana de configuración."""
        # Lista de campos y sus etiquetas
        fields = [
            ("Usuario MySQL:", self.mysql_user_var),
            ("Contraseña MySQL:", self.mysql_pass_var, {"show": "*"}),
            ("Dirección MySQL:", self.mysql_host_var),
            ("Puerto MySQL:", self.mysql_port_var),
        ]

        # Crear y organizar los campos usando grid
        for row, (label_text, var, *kwargs) in enumerate(fields):
            tk.Label(self.settings_window, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky='e')
            entry = tk.Entry(self.settings_window, textvariable=var, **kwargs[0] if kwargs else {})
            entry.grid(row=row, column=1, padx=5, pady=5, sticky='w')

        # Botones de acción
        tk.Button(self.settings_window, text="Guardar", command=self.on_save).grid(
            row=len(fields), column=0, columnspan=2, pady=10, padx=5, sticky='ew'
        )
        tk.Button(self.settings_window, text="Cancelar", command=self.settings_window.destroy).grid(
            row=len(fields) + 1, column=0, columnspan=2, pady=5, padx=5, sticky='ew'
        )

    def on_save(self):
        """Método que se ejecuta al hacer clic en el botón Guardar."""
        self.controller.save_settings()
        
    def get_settings(self):
        """Obtiene los valores actuales de los campos de entrada."""
        return {
            "mysql_user": self.mysql_user_var.get(),
            "mysql_pass": self.mysql_pass_var.get(),
            "mysql_host": self.mysql_host_var.get(),
            "mysql_port": self.mysql_port_var.get(),
        }


class SettingsController:
    def __init__(self, root):
        """Inicializa el controlador de configuración."""
        self.model = SettingsModel()
        self.view = SettingsView(root, self)


        # Cargar configuraciones en la vista
        self.model.load_settings()
        self.load_view_settings()

        # Vincular el evento de guardar
        self.view.on_save = self.save_settings

    def load_view_settings(self):
        """Carga las configuraciones en la vista."""
        settings = self.model.settings
        if settings:
            self.view.mysql_user_var.set(settings.get("mysql_user", ""))
            self.view.mysql_pass_var.set(settings.get("mysql_pass", ""))
            self.view.mysql_host_var.set(settings.get("mysql_host", ""))
            self.view.mysql_port_var.set(settings.get("mysql_port", "3306"))
        else:
            # Establece valores predeterminados si no hay configuraciones
            self.view.mysql_user_var.set("")
            self.view.mysql_pass_var.set("")
            self.view.mysql_host_var.set("")
            self.view.mysql_port_var.set("3306")

    def save_settings(self):
        """Guarda las configuraciones desde la vista al modelo."""
        settings = self.view.get_settings()
        if self.model.save_settings(settings):
            messagebox.showinfo("Éxito", "Configuraciones guardadas correctamente.")
            self.view.settings_window.destroy()


class EntryDetailWindow:
    def __init__(self, root, app, title, item_values=None):
        """Inicializa la ventana de entrada/detalle."""
        self.root = root
        self.app = app
        self.title = title
        self.item_values = item_values
        self.detail_window = tk.Toplevel(self.root)
        self.detail_window.title(title)

        # Make the EntryDetailWindow stay on top
        self.detail_window.wm_transient(self.root)
        
        # Center the EntryDetailWindow on the parent window
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (200 // 2)
        self.detail_window.geometry(f"+{x}+{y}")
        
        self.detail_window.resizable(False, False)
        # Set the focus to the EntryDetailWindow and prevent interaction with the main window
    
        # Variables para los campos de entrada
        self.edit_vars = [tk.StringVar(value=value) for value in (item_values or [""] * 7)]
        self.item_id = None if item_values is None else self.app.tree.selection()[0]
        self.image_display = None
        self.image_path = self.edit_vars[5].get()  # Ruta de la imagen
        
        # Opciones para el tipo de carnet
        self.tipo_carnet_options = ["Profesional", "Gerencial", "Administrativo"]
        self.edit_vars[6].set(item_values[6] if item_values and len(item_values) > 6 else self.tipo_carnet_options[0])

        # Cargar la imagen por defecto
        self.create_ui()
        self.load_image()

        # Agregar un evento para cuando se hace clic en la ventana principal
        self.root.bind("<1>", self.on_root_click)
        # Asegurarse de que la ventana esté visible antes de llamar a grab_set
        self.detail_window.update()  # Forzar la actualización de la ventana
        self.detail_window.grab_set()  # Establecer el foco en la ventana secundaria
        
    def on_root_click(self, event):
        # Setear el foco a la ventana principal
        self.root.focus_set()
        
        # Producir un sonido o parpadeo visual
        self.root.bell()
    
    def load_default_image(self):
        """Carga una imagen en blanco de 100x100 por defecto."""
        img = Image.new('RGB', (100, 100), color=(255, 255, 255))  # Crear una imagen en blanco
        img.thumbnail((100, 100))
        img_tk = ImageTk.PhotoImage(img)
        self.image_display.config(image=img_tk)
        self.image_display.image = img_tk
        self.edit_vars[5].set("")
    
    def create_ui(self):
        """Crea la interfaz de usuario para la ventana de entrada/detalle."""
        labels = ["Nombre", "Apellidos", "Cédula", "Adscrito", "Cargo"]
        for i, label in enumerate(labels):
            tk.Label(self.detail_window, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            if label == "Adscrito":
                # Crear un ComboBox para "Adscrito" usando las abreviaturas de las oficinas
                self.adscrito_combobox = ttk.Combobox(self.detail_window, textvariable=self.edit_vars[3])
                self.adscrito_combobox['values'] = [oficina[1] for oficina in self.app.oficinas]  # Obtener las abreviaturas de las oficinas
                self.adscrito_combobox.grid(row=i, column=1, padx=5, pady=5)
                self.adscrito_combobox.current(0)  # Seleccionar la primera opción por defecto
            else:
                tk.Entry(self.detail_window, textvariable=self.edit_vars[i]).grid(row=i, column=1, padx=5, pady=5)

        # Label para mostrar la miniatura de la imagen
        self.image_display = tk.Label(self.detail_window, bd=2, relief="sunken")
        self.image_display.grid(row=len(labels), column=0, columnspan=2, padx=5, pady=10)

        # Label para mostrar la ruta de la imagen (no editable)
        self.image_path_label = tk.Label(self.detail_window, text="No Hay imagen", bd=2, relief="sunken", wraplength=200)
        self.image_path_label.grid(row=len(labels) + 1, column=0, columnspan=2, padx=5, pady=5, sticky='e')

        # Botón para seleccionar la imagen
        tk.Button(self.detail_window, text="Seleccionar Imagen", command=self.select_image).grid(row=len(labels) + 2, column=0, columnspan=2, padx=5, pady=5)

        # ComboBox para seleccionar el tipo de carnet
        tk.Label(self.detail_window, text="Tipo de Carnet").grid(row=len(labels) + 3, column=0, padx=5, pady=5, sticky='e')
        tipo_carnet_combobox = ttk.Combobox(self.detail_window, textvariable=self.edit_vars[6], values=self.tipo_carnet_options)
        tipo_carnet_combobox.grid(row=len(labels) + 3, column=1, padx=5, pady=5)

        # Botón para guardar nueva entrada o cambios
        action = "Guardar Nueva Entrada" if self.item_values is None else "Guardar Cambios"

        if self.item_values is None:
            # Guardar nueva entrada
            save_command = lambda: self.save_new_entry(self.edit_vars, self.detail_window)
        else:
            # Guardar cambios
            save_command = lambda: self.save_changes(self.edit_vars, self.item_id, self.detail_window)

        tk.Button(
            self.detail_window,
            text=action,
            command=save_command
        ).grid(row=len(labels) + 4, column=0, columnspan=2, padx=5, pady=5)
    
    def select_image(self):
        """Selecciona una imagen para el carnet con manejo de excepciones."""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            try:
                img = Image.open(file_path)
                img.thumbnail((100, 100))
                img_tk = ImageTk.PhotoImage(img)
                self.image_display.config(image=img_tk)
                self.image_display.image = img_tk
                self.edit_vars[5].set(file_path)  # Update the image path variable
                self.image_path_label.config(text=os.path.basename(file_path))  # Muestra solo el nombre del archivo
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la imagen: {str(e)}")
                self.load_default_image()  # Cargar la imagen por defecto si hay un error

    def load_image(self):
        """Carga la imagen en la interfaz."""
        try:
            # Check if the image_path is a valid file and not a directory
            if os.path.isfile(self.image_path):
                img = Image.open(self.image_path)
                img.thumbnail((100, 100))
                img_tk = ImageTk.PhotoImage(img)
                self.image_display.config(image=img_tk)
                self.image_display.image = img_tk
                self.image_path_label.config(text=os.path.basename(self.image_path))  # Muestra solo el nombre del archivo
            else:
                print(f"Invalid image path: {self.image_path}")
                self.load_default_image()
        except Exception as e:
            print(f"Error al cargar la imagen: {e}")
            self.load_default_image()  # Cargar la imagen por defecto si hay un error

    def save_entry(self, edit_vars, detail_window, item_id=None):
        """Guarda una entrada en el Treeview después de validar los campos."""
        # Obtener los valores de los campos
        new_values = [var.get() for var in edit_vars]
        
        # Validación de campos vacíos
        if any(value.strip() == "" for value in new_values[:7]):  # Validar solo los primeros 7 campos
            messagebox.showerror("Error", "Todos los campos deben ser completados.")
            return

        # Validación de la cédula
        if not self.app.is_valid_cedula(new_values[2]):
            messagebox.showerror("Error", "La cédula debe contener solo números y tener 7 u 8 dígitos.")
            return

        # Validación de la existencia del archivo de imagen
        if not os.path.isfile(new_values[5]):
            messagebox.showerror("Error", "El archivo de imagen no existe.")
            return
        
        # Actualizar o agregar la entrada en el Treeview
        if item_id is not None:
            # Actualizar entrada existente
            self.app.tree.item(item_id, values=new_values)
        else:
            # Agregar nueva entrada
            self.app.tree.insert("", "end", values=new_values)

        # Cerrar la ventana de detalles
        detail_window.destroy()

        # Actualizar colores de las filas
        self.app.update_row_colors()  # Actualizar colores después de agregar una nueva entrada
        self.app.update_sidebar()
    
    def save_changes(self, edit_vars, item_id, detail_window):
        """Guarda los cambios en una entrada existente."""
        self.save_entry(edit_vars, detail_window, item_id)

    def save_new_entry(self, edit_vars, detail_window):
        """Guarda una nueva entrada en el Treeview."""
        self.save_entry(edit_vars, detail_window)


class ofiEntryWindow:
    def __init__(self, root, app, title):
        """Inicializa la ventana personalizada con un Treeview y botones de acción."""
        self.root = root
        self.app = app
        self.title = title
        self.custom_window = tk.Toplevel(self.root)
        self.custom_window.title(title)
        
        # Configurar el tamaño de la ventana
        self.custom_window.geometry("400x300")
        
        # Centrar la ventana en la pantalla
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (400 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (300 // 2)
        self.custom_window.geometry(f"+{x}+{y}")
        
        # Hacer que la ventana sea no redimensionable
        self.custom_window.resizable(False, False)
        
        # Variables para almacenar los datos del Treeview
        self.data = self.app.oficinas
        
        # Crear la interfaz de usuario
        self.create_ui()

    def create_ui(self):
        """Crea la interfaz de usuario para la ventana personalizada."""
        # Crear el Treeview
        self.tree = ttk.Treeview(self.custom_window, columns=("Nombre", "Abreviatura"), show="headings")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Abreviatura", text="Abreviatura")
        self.tree.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        # Agregar la información de self.app.oficinas al Treeview
        for oficina in self.app.oficinas:
            self.tree.insert("", "end", values=oficina)
        
        # Crear los botones de acción
        self.add_button = tk.Button(self.custom_window, text="Agregar", command=self.open_add_edit_window)
        self.add_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.edit_button = tk.Button(self.custom_window, text="Editar", command=self.open_add_edit_window)
        self.edit_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.delete_button = tk.Button(self.custom_window, text="Eliminar", command=self.delete_entry)
        self.delete_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        self.accept_button = tk.Button(self.custom_window, text="Aceptar", command=self.accept_changes)
        self.accept_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.cancel_button = tk.Button(self.custom_window, text="Cancelar", command=self.cancel_changes)
        self.cancel_button.grid(row=2, column=2, padx=5, pady=5, sticky="ew")
        
        # Configurar el peso de las filas y columnas para que se expandan correctamente
        self.custom_window.grid_rowconfigure(0, weight=1)
        self.custom_window.grid_columnconfigure(0, weight=1)
        self.custom_window.grid_columnconfigure(1, weight=1)
        self.custom_window.grid_columnconfigure(2, weight=1)
        
        # Mantener la ventana siempre encima
        self.custom_window.attributes("-topmost", True)

    def open_add_edit_window(self):
        """Abre una ventana para agregar o editar una entrada."""
        self.add_edit_window = tk.Toplevel(self.custom_window)
        self.add_edit_window.title("Agregar/Editar Entrada")
        
        # Centrar la ventana en la pantalla
        x = self.custom_window.winfo_x() + (self.custom_window.winfo_width() // 2) - (200 // 2)
        y = self.custom_window.winfo_y() + (self.custom_window.winfo_height() // 2) - (100 // 2)
        self.add_edit_window.geometry(f"+{x}+{y}")
        
        # Hacer que la ventana sea no redimensionable
        self.add_edit_window.resizable(False, False)
        
        # Variables para los campos de entrada
        self.nombre_var = tk.StringVar()
        self.abreviatura_var = tk.StringVar()
        
        # Crear la interfaz de usuario para la ventana de agregar/editar
        tk.Label(self.add_edit_window, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(self.add_edit_window, textvariable=self.nombre_var).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.add_edit_window, text="Abreviatura:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(self.add_edit_window, textvariable=self.abreviatura_var).grid(row=1, column=1, padx=5, pady=5)

        # Botones de Aceptar y Cancelar
        tk.Button(self.add_edit_window, text="Aceptar", command=self.save_entry).grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        tk.Button(self.add_edit_window, text="Cancelar", command=self.add_edit_window.destroy).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        # Mantener la ventana siempre encima
        self.add_edit_window.attributes("-topmost", True)
        # Bloquear la interacción con el ofiEntryWindow
        self.add_edit_window.grab_set()
        
    def save_entry(self):
        """Guarda la entrada en el Treeview y en el atributo data."""
        nombre = self.nombre_var.get()
        abreviatura = self.abreviatura_var.get()
        
        if nombre and abreviatura:
            # Comprobación para no tener una entrada repetida
            if (nombre, abreviatura) in self.data:
                messagebox.showerror("Error", "Entrada repetida. No se puede agregar una entrada con el mismo nombre y abreviatura.", parent=self.add_edit_window)
            elif nombre in [oficina[0] for oficina in self.data]:
                messagebox.showerror("Error", "Nombre existente. No se puede agregar una entrada con el mismo nombre.", parent=self.add_edit_window)
            elif abreviatura in [oficina[1] for oficina in self.data]:
                messagebox.showerror("Error", "Abreviatura existente. No se puede agregar una entrada con la misma abreviatura.", parent=self.add_edit_window)
            else:
                self.data.append((nombre, abreviatura))
                self.tree.insert("", "end", values=(nombre, abreviatura))
                self.add_edit_window.destroy()

    def delete_entry(self):
        """Elimina la entrada seleccionada del Treeview y del atributo data."""
        selected_item = self.tree.selection()
        if selected_item:
            self.tree.delete(selected_item)
            self.data = [self.tree.item(item, 'values') for item in self.tree.get_children()]

    def accept_changes(self):
        """Acepta los cambios realizados en la ventana."""
        # Aquí puedes agregar la lógica para manejar los cambios aceptados
        self.app.oficinas = self.data  # Guardar los datos en el atributo oficinas
        self.custom_window.destroy()
    
    def cancel_changes(self):
        """Pregunta si se está seguro de cancelar los cambios."""
        respuesta = messagebox.askyesno("Cancelar cambios", "¿Estás seguro de cancelar los cambios?", parent=self.custom_window)
        if respuesta:
            self.custom_window.destroy()
        else:
            pass  # No hacer nada si la respuesta es no


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()