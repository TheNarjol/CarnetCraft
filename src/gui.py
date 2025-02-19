import pandas as pd # type: ignore
import tkinter as tk
import os
import logging
import json
from tkinter import filedialog, messagebox, Menu
from tkinter import ttk
import traceback
import io

from funcion import crear_image_thumbnail_binarios, convertir_str_a_bytes


# Asegúrate de tener la clase ImageGenerator implementada
from image_generator import ImageGenerator
from database_manager import DatabaseManager
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
        self.database_manager = DatabaseManager()
        self.get_oficinas()
        
        
        self.tipo_carnet_options = self.get_tipo_carnet_options()

        # Iniciar la ventana maximizada
        self.maximize_window()  # Método para manejar la maximización
        
        # Crear una barra de menú
        self.create_menu_bar()
        
        # Crear el Frame principal para el Treeview y el Sidebar
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10, side=tk.BOTTOM)
        
        # Crear el sidebar
        self.sidebar = tk.Frame(self.main_frame, width=200, bg="lightgray")
        self.sidebar.pack(side="right", fill="y", padx=10, pady=10)
        self.sidebar.pack_propagate(False)  # Evitar que el sidebar se expanda automáticamente
        
        # Crear el frame para los botones de navegación
        self.pagination_frame = tk.Frame(self.main_frame)
        self.pagination_frame.pack(fill="y", pady=10, side=tk.BOTTOM)
        
        # Crear el frame para los botones de Control
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(fill="x", pady=10)
        
        self.filter_frame = tk.Frame(self.root)
        self.filter_frame.pack(pady=5, padx=10, side=tk.TOP, fill=tk.X)
        
        # Crear el Treeview y los botones de selección
        self.create_treeview_and_buttons()
        
        # Crear el Sidebar
        self.create_sidebar()
        self.create_filter()
        
        # DataFrame para almacenar los datos
        self.df = None


        # Instancia del generador de imágenes
        self.image_generator = ImageGenerator()

        # Configurar tags para colores
        self.tree.tag_configure('missing_data', background='yellow')
        self.tree.tag_configure('error_data', background='red')
        
        # Cargar una imagen en blanco de 100x100 por defecto
        self.load_default_image()
        self.fill_tree()
        self.update_row_colors()

    def get_tipo_carnet_options(self):
        # Obtener los tipos de carnet de la base de datos o de un archivo de configuración
        # ...
        return ["Profesional", "Gerencial", "Administrativo", "Coordinadores", "Obrero", "Seguridad"]
    
    def get_oficinas(self):
        # Obtener los nombres de las oficinas de la base de datos o de un archivo de configuración
        # ...
        self.oficinas = self.database_manager.fetch_oficinas()
    
    def fill_tree(self, adscrito=None, tipo=None, page=1):
        self.clear_treeview()
        data = self.database_manager.fetch_data(adscrito, tipo, page)
        for row in data:
            self.tree.insert("", "end", values=row)
        self.pages = -(-len(data) // 25)  # Calcula el número de páginas necesarias
        

        # Agregar botones de navegación por páginas
        self.add_pagination_buttons()
        self.update_row_colors()

    def add_pagination_buttons(self):
        # Eliminar los botones de navegación existentes
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()

        if self.pages > 1:
            # Agregar botones de navegación
            for i in range(self.pages):
                button = tk.Button(self.pagination_frame, text=str(i+1), command=lambda page=i+1: self.fill_tree(adscrito, tipo, page))
                button.pack(side=tk.LEFT, padx=5)
    
    def clear_treeview(self):
        # Limpiar el contenido del Treeview
        self.tree.delete(*self.tree.get_children())

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
    
    def create_filter(self):
        #Filtros
        self.search_label = tk.Label(self.filter_frame, text="Buscar por cédula:")
        self.search_label.pack(side=tk.LEFT, padx=5)

        self.search_entry = tk.Entry(self.filter_frame)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        self.search_button = tk.Button(self.filter_frame, text="Buscar", command=self.search_by_cedula)
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.adscrito_label = tk.Label(self.filter_frame, text="Adscrito:")
        self.adscrito_label.pack(side=tk.LEFT, padx=5)

        self.adscrito_var = tk.StringVar()
        self.adscrito_combobox = ttk.Combobox(self.filter_frame, textvariable=self.adscrito_var)
        self.adscrito_combobox['values'] = [oficina[0] for oficina in self.oficinas]  # Obtener los nombres de las oficinas
        self.adscrito_combobox.pack(side=tk.LEFT, padx=5)

        self.adscrito_clear_button = tk.Button(self.filter_frame, text="x", command=self.clear_adscrito_filter)
        self.adscrito_clear_button.pack(side=tk.LEFT, padx=5)

        self.tipo_label = tk.Label(self.filter_frame, text="Tipo:")
        self.tipo_label.pack(side=tk.LEFT, padx=5)

        self.tipo_var = tk.StringVar()
        self.tipo_combobox = ttk.Combobox(self.filter_frame, textvariable=self.tipo_var)
        self.tipo_combobox['values'] = self.tipo_carnet_options  # Obtener los tipos de carnet
        self.tipo_combobox.pack(side=tk.LEFT, padx=5)

        self.tipo_clear_button = tk.Button(self.filter_frame, text="x", command=self.clear_tipo_filter)
        self.tipo_clear_button.pack(side=tk.LEFT, padx=5)

        self.filter_button = tk.Button(self.filter_frame, text="Filtrar", command=self.filter_data)
        self.filter_button.pack(side=tk.LEFT, padx=5)
        
    def create_treeview_and_buttons(self):
        """Crea el Treeview y los botones de selección."""
        # Botón para crear una nueva entrada
        self.new_entry_button = tk.Button(
            self.control_frame, text="Agregar", command=self.open_new_entry_window
        )

        self.new_entry_button.pack(pady=5, anchor="w", padx=10, side=tk.LEFT)
        
        # Botón para seleccionar o deseleccionar todos
        self.select_all_button = tk.Button(
            self.control_frame,
            text="Seleccionar Todos",
            command=self.toggle_select_all,
        )
        self.select_all_button.pack(pady=5, anchor="w", padx=10, side=tk.LEFT)
        
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
        
    def clear_adscrito_filter(self):
        self.adscrito_var.set("")
        self.filter_data()

    def clear_tipo_filter(self):
        self.tipo_var.set("")
        self.filter_data()
        
    def filter_data(self):
        adscrito = self.adscrito_combobox.get()
        tipo = self.tipo_combobox.get()
        for oficina in self.oficinas:
            if oficina[0] == adscrito:
                adscrito = oficina[1]
                break
        self.fill_tree(adscrito, tipo)
    
    def search_by_cedula(self):
        cedula = self.search_entry.get()
        # Buscar en la base de datos o en el archivo de datos
        data = self.database_manager.fetch_data_by_cedula(cedula)
        if data:
            # Mostrar la entrada encontrada
            self.tree.delete(*self.tree.get_children())
            self.tree.insert("", "end", values=data)
        else:
            # Mostrar un mensaje de error
            messagebox.showerror("Error", "No se encontró la cédula")
    
    def create_sidebar(self):
        """Crea el sidebar con los labels y el botón de editar."""
        
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
        
        # Botón para Eliminar
        self.delete_button = tk.Button(
            self.sidebar, text="Eliminar", command=self.delete_entry, state="disabled"
            )
        self.delete_button.pack(side="bottom", fill="x", pady=5)
        
        # Botón para generar imágenes
        self.generate_button = tk.Button(
            self.sidebar, text="Generar Imágenes", command=self.generate_images, state="disabled")
        self.generate_button.pack(side="bottom", pady=5, padx=5, fill="x")
        
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
            self.delete_button.config(state="disabled")  # Activar el botón "ekiminar"
                        
            self.generate_button.config(state="disabled")  # Activar el botón "general"
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
            
            self.delete_button.config(state="normal")  # Activar el botón "ekiminar"
            self.delete_button.pack(side="bottom", fill="x", pady=5)  # Asegurarse de que el botón esté visible
            
            self.generate_button.config(state="normal")  # Activar el botón "ekiminar"
            self.generate_button.pack(side="bottom", fill="x", pady=5)  # Asegurarse de que el botón esté visible

        else:
            # Selección múltiple
            self.selection_status_label.config(text="Selección múltiple")
            self.selection_status_label.pack(pady=10)  # Mostrar el label
            for label in self.sidebar_labels.values():
                label.pack_forget()  # Ocultar los labels de detalles
            self.clear_image_display()  # Limpiar la imagen
            self.edit_button.config(state="disabled")  # Desactivar el botón "Editar"
            self.generate_button.config(state="normal")  # Activar el botón "general"

    def delete_entry(self):
        selected_items = self.tree.selection()
        total = 0
        eliminado = 0
        mantenido = 0
        if selected_items:
            for item in selected_items:
                    total += 1
                    item_values = self.tree.item(item, 'values')
                    respuesta = messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de eliminar el registro de {item_values[0]} {item_values[1]} con cédula {item_values[2]}?")
                    if respuesta:
                        eliminado += 1
                        self.database_manager.delete_entry(item_values[2])
                        self.tree.delete(item)
                    else:
                        mantenido += 1            
        else:
            messagebox.showerror("Error", "No se ha seleccionado ningún registro para eliminar.")
        # después de agregar los datos
        messagebox.showinfo("Eliminar", f"Se Elimaron {eliminado} registros, {mantenido} sin cambios  \n  {total} registros en total.")
        self.update_sidebar()
            
    def load_image_thumbnail(self, img_path):
        """Carga y muestra la miniatura de la imagen en el sidebar."""
        
        try:
            binario = convertir_str_a_bytes(img_path)
            img = crear_image_thumbnail_binarios(binario)
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
        agregados = 0
        actualizados = 0
        no_actualizados = 0
        errores = 0
        total = 0

        # Lista de tipos de carnet permitidos
        tipos_carnet_permitidos = ["Profesional", "Gerencial", "Administrativo", "Coordinadores", "Obrero", "Seguridad"]  # Reemplaza con los tipos de carnet válidos

        # Oficina predeterminada en caso de no coincidir
        oficina_predeterminada = self.oficinas[0][1]  # Abreviatura de la oficina predeterminada

        for index, row in self.df.iterrows():
            values = [
                row.get("Nombre", ""),
                row.get("Apellidos", ""),
                row.get("Cedula", ""),
                row.get("Adscrito", ""),
                row.get("Cargo", ""),
                row.get("Imagen", ""),  # Campo para la ruta de la imagen
                row.get("Tipo", "")  # Campo para el tipo de carnet
            ]
            total += 1

            # Verificar si el tipo de carnet es válido
            if values[6] not in tipos_carnet_permitidos:
                # Si no es válido, asignar el valor predeterminado (primer tipo de carnet permitido)
                values[6] = tipos_carnet_permitidos[0]
                print(f"Advertencia: Tipo de carnet no válido. Se asignó el valor predeterminado: {tipos_carnet_permitidos[0]}")

            # Verificar si el campo "adscrito" coincide con una abreviatura o nombre de oficina
            adscrito = values[3]
            oficina_encontrada = None

            # Buscar si el adscrito coincide con una abreviatura o nombre de oficina
            for oficina in self.oficinas:
                if adscrito == oficina[1]:  # Si coincide con una abreviatura
                    oficina_encontrada = oficina[1]  # Dejar la abreviatura
                    break
                elif adscrito == oficina[0]:  # Si coincide con un nombre
                    oficina_encontrada = oficina[1]  # Cambiar por la abreviatura
                    break

            # Si no se encontró coincidencia, asignar la oficina predeterminada
            if not oficina_encontrada:
                oficina_encontrada = oficina_predeterminada
                print(f"Advertencia: Adscrito '{adscrito}' no coincide con ninguna oficina. Se asignó la oficina predeterminada: {oficina_predeterminada}")

            # Actualizar el valor de adscrito en los valores
            values[3] = oficina_encontrada

            if values[0] and values[1] and values[2]:  # Verificar si NOMBRE, APELLIDO y CEDULA tienen información
                print(values)
                if self.database_manager.check_duplicate_by_cedula(values[2]):
                    # Si el registro está repetido, actualizarlo
                    respuesta = messagebox.askyesno("Confirmar actualización", f"¿Estás seguro de actualizar el registro de {values[0]} {values[1]} con cédula {values[2]}?")
                    if respuesta:
                        # Obtener los valores actuales del registro
                        registro_actual = self.database_manager.fetch_data_by_cedula(values[2])
                        # Actualizar solo los campos que no están vacíos
                        new_values = {
                            'nombre': registro_actual[1] if values[0] else registro_actual[1],
                            'apellidos': registro_actual[2] if values[1] else registro_actual[2],
                            'cedula': values[2],
                            'adscrito': values[3],  # Usar el valor actualizado de adscrito
                            'cargo': registro_actual[5] if values[4] else registro_actual[5],
                            'imagen': registro_actual[6] if values[5] else registro_actual[6],
                            't ipo_carnet': registro_actual[7] if values[6] else registro_actual[7]
                        }
                        self.database_manager.update_entry(new_values)
                        actualizados += 1
                    elif not respuesta:
                        no_actualizados += 1
                    else:
                        errores += 1
                else:
                    # Si el registro no está repetido, agregarlo a la base de datos
                    self.database_manager.save_new_entry({
                        'nombre': values[0],
                        'apellidos': values[1],
                        'cedula': values[2],
                        'adscrito': values[3],  # Usar el valor actualizado de adscrito
                        'cargo': values[4],
                        'imagen': values[5],
                        'tipo_carnet': values[6]
                    })
                    agregados += 1
            else:
                errores += 1

        confirmation_window.destroy()  # Cerrar la ventana de confirmación
        self.fill_tree()  # Actualizar el Treeview con los nuevos datos
        self.update_row_colors()  # Actualizar colores después de agregar los datos
        messagebox.showinfo("Resumen", f"Se agregaron {agregados} registros nuevos, se actualizaron {actualizados}, no se actualizaron {no_actualizados} registros y se encontraron {errores} errores. \n Se encontraron {total} registros en total.")
    
    def reemplazar_abreviatura_oficina(self, data_row):
        """
        Reemplaza la abreviatura de la oficina en la fila de datos por el nombre completo.

        Parámetros:
        - data_row: Una tupla que contiene los datos de una fila.

        Retorna:
        - La misma fila de datos con la abreviatura de la oficina reemplazada por el nombre completo.
        """
        # Obtener la abreviatura de la oficina
        oficina_abreviatura = data_row[3]
        
        # Buscar el nombre completo de la oficina correspondiente a la abreviatura
        oficina_nombre = next((oficina[0] for oficina in self.oficinas if oficina[1] == oficina_abreviatura), None)
        
        # Si se encuentra el nombre completo, reemplazar la abreviatura
        if oficina_nombre:
            data_row = list(data_row)  # Convertir a lista para poder modificar
            data_row[3] = oficina_nombre  # Reemplazar la abreviatura por el nombre completo
            data_row = tuple(data_row)  # Convertir de vuelta a tupla
        
        return data_row

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
        total_carnets = 0
        errores = []
        column = ["Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "RutaImagen", "TipoCarnet"]

        for item in selected_items:
            data_row = self.tree.item(item)["values"]
            data_row = self.reemplazar_abreviatura_oficina(data_row)
            if not self.validate_fields(data_row):
                messagebox.showerror("Error", "Todos los campos deben ser completados y válidos.")
                total_errores += 1
                continue
            
            try:
                # Generar la imagen y guardarla en la nueva carpeta
                data = dict(zip(column, data_row))
                
                # Generar el nombre del archivo
                image_filename = self.image_generator.generate_carnet(data)

                # Verificar si el archivo ya existe en el directorio de destino
                base_filename = os.path.basename(image_filename)  # Obtener el nombre base del archivo
                name, ext = os.path.splitext(base_filename)  # Separar el nombre y la extensión
                counter = 1  # Inicializar el contador

                # Bucle para encontrar un nombre de archivo no usado
                while True:
                    # Construir el nombre del archivo con el contador
                    new_image_filename = f"{name}_{counter}{ext}" if counter > 1 else f"{name}{ext}"
                    new_image_path = os.path.join(full_path, new_image_filename)  # Ruta completa del archivo

                    # Verificar si el archivo ya existe
                    if not os.path.exists(new_image_path):
                        break  # Salir del bucle si el archivo no existe
                    counter += 1  # Incrementar el contador si el archivo existe

                # Mover la imagen generada a la carpeta con el nuevo nombre
                os.rename(image_filename, new_image_path)
                total_generados += 1  # Incrementar contador de generados
            
            except FileNotFoundError as fnf_error:
                total_errores += 1
                errores.append(f"Archivo no encontrado: {str(fnf_error)}")
                print(str(e))
                logging.error(f"Archivo no encontrado: {str(fnf_error)} - {data_row[0]} {data_row[1]} (Cédula: {data_row[2]})")
            except PermissionError as perm_error:
                total_errores += 1
                errores.append(f"Permiso denegado al acceder a: {str(perm_error)}")
                print(str(e))
                logging.error(f"Permiso denegado: {str(perm_error)} - {data_row[0]} {data_row[1]} (Cédula: {data_row[2]})")
            except Exception as e:
                total_errores += 1
                error_message = f"Error al generar imagen para {data_row[0]} {data_row[1]} (Cédula: {data_row[2]}):"
                print(str(e))
                error_details = traceback.format_exc()  # Captura la traza del error
                errores.append(f"{error_message}\nDetalles del error:\n{str(e)}")
                print(error_details)
                logging.error(f"No se pudo generar la imagen para {data_row[6]}: {str(e)} - {data_row[0]} {data_row[1]} (Cédula: {data_row[2]})\nDetalles del error:\n{error_details}")
            total_carnets += 1

        # Mensaje final con el resumen de la operación
        if total_errores > 0:
            error_message = "\n".join(errores)
            messagebox.showerror(
                "Errores en la generación",
                f"Se generaron {total_carnets} / {total_generados} carnets con éxito.\n"
                f"Se encontraron errores en {total_errores} carnets:\n{error_message}"
                )
        else:
            messagebox.showinfo(
                "Éxito", f"Todas las imágenes seleccionadas han sido generadas. Total: {total_carnets} / {total_generados}"
            )

    def is_valid_name(self, name):
        """
        Valida que el nombre no contenga números ni caracteres especiales.

        Parámetros:
        - name: El nombre a validar.

        Retorna:
        - True si el nombre es válido, False en caso contrario.
        """
        return name.replace(" ", "").isalpha()

    def is_valid_cedula(self, cedula):
        """
        Valida que la cédula contenga solo números y tenga 7 u 8 dígitos.

        Parámetros:
        - cedula: La cédula a validar.

        Retorna:
        - True si la cédula es válida, False en caso contrario.
        """
        cedula_str = str(cedula)
        return  len(cedula_str) in (7, 8)
    
    def validate_row(self, values):
        """
        Valida si una fila tiene datos faltantes o errores.
        Devuelve el tag correspondiente ('missing_data', 'error_data') o None si no hay problemas.
        """
        # Extraer valores
        nombre = values[0]
        apellidos = values[1]
        cedula = values[2]
        ruta_imagen = values[5]

        # Verificar datos faltantes
        if not nombre or not apellidos or not cedula or not ruta_imagen:
            return 'missing_data'

        # Verificar errores en la cédula
        if not self.is_valid_cedula(cedula):
            return 'error_data'

        return None  # No hay errores ni datos faltantes
    
    def validate_fields(self, values):
        """
        Valida que los campos no estén vacíos, que la cédula sea válida, que el archivo de imagen exista y que los nombres no contengan números ni caracteres especiales.

        Parámetros:
        - values: Una lista de valores que corresponden a los campos.

        Retorna:
        - True si todos los campos son válidos, False en caso contrario.
        """
        return (all(values[:7]) and 
                self.is_valid_cedula(values[2]) and 
                self.is_valid_name(values[0]) and 
                self.is_valid_name(values[1]))
    
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
        ofiEntryWindow(self.root, self, self.database_manager)


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
        self.tipo_carnet_options = ["Profesional", "Gerencial", "Administrativo", "Coordinadores", "Obrero", "Seguridad"]
        self.edit_vars[6].set(item_values[6] if item_values and len(item_values) > 6 else self.tipo_carnet_options[0])

        # Cargar la imagen por defecto
        self.create_ui()
        self.load_image()

        # Asegurarse de que la ventana esté visible antes de llamar a grab_set
        self.detail_window.update()  # Forzar la actualización de la ventana
        
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
        # Función de validación para limitar el número de caracteres
        def validate_length(text, max_length):
            max_length = int(max_length)  # Convertir max_length a entero
            return len(text) <= max_length
        
        # Registrar la función de validación
        vcmd = (self.detail_window.register(validate_length), '%P', '%d')

        
        for i, label in enumerate(labels):
            tk.Label(self.detail_window, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            if label == "Adscrito":
                # Crear un ComboBox para "Adscrito" usando las abreviaturas de las oficinas
                self.adscrito_combobox = ttk.Combobox(self.detail_window, textvariable=self.edit_vars[3])
                self.adscrito_combobox['values'] = [oficina[1] for oficina in self.app.oficinas]  # Obtener las abreviaturas de las oficinas
                self.adscrito_combobox.grid(row=i, column=1, padx=5, pady=5)
                self.adscrito_combobox.current(0)  # Seleccionar la primera opción por defecto
            else:
                # Crear un campo de entrada (Entry) con límite de caracteres
                entry = tk.Entry(self.detail_window, textvariable=self.edit_vars[i])
                if label == "Nombre" or label == "Apellidos":
                    # Limitar a 20 caracteres
                    entry.config(validate="key", validatecommand=(vcmd[0], '%P', 24))
                elif label == "Cargo":
                    # Limitar a 25 caracteres
                    entry.config(validate="key", validatecommand=(vcmd[0], '%P', 25))
                entry.grid(row=i, column=1, padx=5, pady=5)

        
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

        save_command = lambda: self.save_entry(self.edit_vars, self.detail_window, self.item_id)

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
        """Carga la imagen en la interfaz, verificando su tamaño y redimensionando si es necesario."""
        try:
            # Check if the image_path is a valid file and not a directory
            if os.path.isfile(self.image_path):
                # Si image_path es una ruta válida, se trata de una imagen en disco
                img = Image.open(self.image_path)
                self.image_path_label.config(text=os.path.basename(self.image_path))  # Muestra solo el nombre del archivo
            elif any(not char.isprintable() for char in self.image_path):
                # Si image_path es un bytes, se trata de binarios
                byna = convertir_str_a_bytes(self.image_path)
                img = crear_image_thumbnail_binarios(byna)
                self.image_path_label.config(text="Archivo")
            else:
                print(f"Invalid image path: {self.image_path}")
                self.load_default_image()
                return

            # Obtener las dimensiones de la imagen
            width, height = img.size

            # Verificar si la imagen es menor a 300x300
            if width < 300 or height < 300:
                print("Advertencia: La imagen es demasiado pequeña. Debe ser al menos de 300x300 píxeles.")
                self.load_default_image()
                return

            # Verificar si la imagen es mayor a 400x400 y redimensionar si es necesario
            if width > 400 or height > 400:
                # Calcular el nuevo tamaño manteniendo la proporción
                ratio = max(300 / width, 300 / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Redimensionar la imagen para mostrarla en la interfaz
            img.thumbnail((100, 100))
            img_tk = ImageTk.PhotoImage(img)
            self.image_display.config(image=img_tk)
            self.image_display.image = img_tk

        except Exception as e:
            print(f"Error al cargar la imagen: {e}")
            self.load_default_image()  # Cargar la imagen por defecto si hay un error
            
    def save_entry(self, edit_vars, detail_window, item_id=None):
        """
        Guarda una entrada en la base de datos o modifica un registro existente si la cédula ya existe.

        Parámetros:
        - edit_vars: Variables para los campos de entrada.
        - detail_window: Ventana de detalles.
        - item_id: ID del item en el Treeview (opcional).
        """
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
        if os.path.isfile(new_values[5]):
            # Convertir la imagen a binario
            image_path = new_values[5]
            with open(image_path, 'rb') as image_file:
                image_binary = image_file.read()
            new_values[5] = image_binary
        elif any(not char.isprintable() for char in new_values[5]):
            new_values[5] = convertir_str_a_bytes(new_values[5])
        else:
            messagebox.showerror("Error", "El archivo de imagen no existe.")
            return

        # Actualizar o agregar la entrada en el Treeview
        if item_id is not None:
            # Actualizar entrada existente
            self.app.tree.item(item_id, values=new_values)

        else:
            # Agregar nueva entrada
            self.app.tree.insert("", "end", values=new_values)

        # Verificar si la cédula ya existe en la base de datos
        if self.app.database_manager.check_duplicate_by_cedula(new_values[2]):
            # Si la cédula ya existe, modificar el registro existente
            self.app.database_manager.update_entry({
                'nombre': new_values[0],
                'apellidos': new_values[1],
                'cedula': new_values[2],
                'adscrito': new_values[3],
                'cargo': new_values[4],
                'imagen': new_values[5],
                'tipo_carnet': new_values[6]
            })
        else:
            # Si la cédula no existe, guardar una nueva entrada
            self.app.database_manager.save_new_entry({
                'nombre': new_values[0],
                'apellidos': new_values[1],
                'cedula': new_values[2],
                'adscrito': new_values[3],
                'cargo': new_values[4],
                'imagen': new_values[5],
                'tipo_carnet': new_values[6]
            })

        # Actualizar el Treeview
        self.app.update_row_colors()
        self.app.update_sidebar()

        self.app.root.focus_set()
        # Cerrar la ventana de detalles
        detail_window.destroy()
    
    def save_changes(self, edit_vars, item_id, detail_window):
        """Guarda los cambios en una entrada existente."""
        self.save_entry(edit_vars, detail_window, item_id)

    def save_new_entry(self, edit_vars, detail_window):
        """Guarda una nueva entrada en el Treeview."""
        self.save_entry(edit_vars, detail_window)


class EditOficinaWindow:
    def __init__(self, parent, database_manager, ofi_entry_window, id_oficina=None, nombre_oficina=None, codigo_oficina=None):
        """
        Inicializa la ventana de edición de oficinas.

        Parámetros:
        - parent: Ventana principal o contenedor.
        - database_manager: Instancia de DatabaseManager para interactuar con la base de datos.
        - id_oficina (int): ID de la oficina a editar (opcional).
        - nombre_oficina (str): Nombre de la oficina a editar (opcional).
        - codigo_oficina (str): Código de la oficina a editar (opcional).
        """
        print(nombre_oficina, codigo_oficina, id_oficina)
        self.parent = parent
        self.database_manager = database_manager
        self.ofi_entry_window = ofi_entry_window  # Guardar la instancia de ofiEntryWindow
        self.id_oficina = id_oficina
        self.nombre_oficina = nombre_oficina
        self.codigo_oficina = codigo_oficina
        self.setup_ui()

    def setup_ui(self):
        """
        Configura la interfaz de usuario de la ventana de edición.
        """
        self.window = tk.Toplevel(self.parent)
        self.window.title("Editar Oficina" if self.id_oficina else "Agregar Oficina")

        # Campos de entrada
        tk.Label(self.window, text="Nombre de la oficina:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_nombre = tk.Entry(self.window)
        self.entry_nombre.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Código de la oficina:").grid(row=1, column=0, padx=10, pady=5)
        self.entry_codigo = tk.Entry(self.window)
        self.entry_codigo.grid(row=1, column=1, padx=10, pady=5)

        # Llenar campos si se está editando una oficina
        if self.id_oficina:
            self.entry_nombre.insert(0, self.nombre_oficina)
            self.entry_codigo.insert(0, self.codigo_oficina)

        # Botón para guardar o actualizar
        button_text = "Actualizar" if self.id_oficina else "Guardar"
        tk.Button(self.window, text=button_text, command=self.save).grid(row=2, column=0, columnspan=2, pady=10)

    def save(self):
        """
        Guarda o actualiza la oficina en la base de datos.
        """
        nuevo_nombre = self.entry_nombre.get()
        nuevo_codigo = self.entry_codigo.get()

        if self.id_oficina:
            # Actualizar la oficina existente
            if self.database_manager.update_oficina(self.id_oficina, nuevo_nombre, nuevo_codigo):
                messagebox.showinfo("Éxito", "Oficina actualizada correctamente.")
            else:
                messagebox.showerror("Error", "No se pudo actualizar la oficina.")
                
        else:
            # Aquí puedes implementar la lógica para agregar una nueva oficina si es necesario save_oficina
            if self.database_manager.save_oficina( nuevo_nombre, nuevo_codigo):
                messagebox.showinfo("Éxito", "Oficina Agregada correctamente.")
            else:
                messagebox.showerror("Error", "No se pudo actualizar la oficina.")
        self.ofi_entry_window.load_oficinas()
        self.window.destroy()

        
class ofiEntryWindow:
    def __init__(self, parent, ImageGeneratorApp ,database_manager):
        """
        Inicializa la ventana para gestionar oficinas.

        Parámetros:
        - parent: Ventana principal o contenedor.
        - database_manager: Instancia de DatabaseManager para interactuar con la base de datos.
        """
        self.parent = parent
        self.ImageGeneratorApp = ImageGeneratorApp
        self.database_manager = database_manager
        self.setup_ui()
        self.load_oficinas()  # Carga las oficinas al iniciar la ventana

    def setup_ui(self):
        """
        Configura la interfaz de usuario de la ventana.
        """
        self.window = tk.Toplevel(self.parent)
        self.window.title("Gestión de Oficinas")

        # Configuración del Treeview
        self.tree = ttk.Treeview(self.window, columns=( "Nombre", "Código"), show="headings")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Código", text="Código")
        self.tree.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        # Botones
        tk.Button(self.window, text="Agregar", command=self.open_add_window).grid(row=1, column=0, padx=5, pady=10)
        tk.Button(self.window, text="Modificar", command=self.open_edit_window).grid(row=1, column=1, padx=5, pady=10)
        tk.Button(self.window, text="Eliminar", command=self.delete_entry).grid(row=1, column=2, padx=5, pady=10)

        tk.Button(self.window, text="guardar", command=self.save_tree).grid(row=1, column=3, padx=5, pady=10)

        
        # Asignar evento de selección en el Treeview
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_oficinas(self):
        """
        Carga la lista de oficinas desde la base de datos y la muestra en el Treeview.
        """
        # Limpiar el Treeview antes de cargar nuevos datos
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Obtener las oficinas desde la base de datos (incluyendo el ID)
        oficinas = self.database_manager.fetch_oficinas_with_id()
        if oficinas:
            for oficina in oficinas:
                self.tree.insert("", "end", values=(oficina[1], oficina[2], oficina[0]))  # (ID, Nombre, Código)
    
    def save_tree(self):
        self.ImageGeneratorApp.get_oficinas()
        self.ImageGeneratorApp.update_sidebar()
        self.ImageGeneratorApp.clear_treeview()
        self.ImageGeneratorApp.fill_tree()
        self.window.destroy()
        
    def on_select(self, event):
        """
        Maneja la selección de una oficina en el Treeview.
        """
        self.selected_item = self.tree.selection()
        if self.selected_item:
            self.selected_values = self.tree.item(self.selected_item, "values")

    def open_add_window(self):
        """
        Abre la ventana para agregar una nueva oficina.
        """
        EditOficinaWindow(parent = self.window, database_manager = self.database_manager, ofi_entry_window=self)

    def open_edit_window(self):
        """
        Abre la ventana para editar una oficina seleccionada.
        """
        if hasattr(self, "selected_item") and self.selected_item:
                id_oficina = self.selected_values[2]  # Código
                nombre_oficina = self.selected_values[0]  # Nombre
                codigo_oficina = self.selected_values[1]  # Nombre
                EditOficinaWindow(self.window, self.database_manager, self, id_oficina, nombre_oficina, codigo_oficina)
        else:
            messagebox.showwarning("Selección requerida", "Por favor, seleccione una oficina para editar.")

    def delete_entry(self):
        """
        Elimina una oficina de la base de datos usando su ID.
        """
        if hasattr(self, "selected_item") and self.selected_item:
            # Obtener el ID de la oficina seleccionada
            id_oficina = self.selected_values[2]  # El ID es el primer valor en el Treeview

            # Pedir confirmación al usuario
            confirmacion = messagebox.askyesno(
                "Confirmar",
                "¿Está seguro de que desea eliminar esta oficina?"
            )

            if confirmacion:
                # Eliminar la oficina usando el ID
                if self.database_manager.delete_oficina(id_oficina):
                    messagebox.showinfo("Éxito", "Oficina eliminada correctamente.")
                    self.load_oficinas()  # Recargar la lista de oficinas
                else:
                    messagebox.showerror("Error", "No se pudo eliminar la oficina.")
        else:
            messagebox.showwarning("Selección requerida", "Por favor, seleccione una oficina para eliminar.") 


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()