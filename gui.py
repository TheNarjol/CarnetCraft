import pandas as pd
import tkinter as tk
import os
import logging
from tkinter import filedialog, messagebox, Menu
from tkinter import ttk
from image_generator import ImageGenerator  # Asegúrate de tener la clase ImageGenerator implementada
from PIL import Image, ImageTk  # Asegúrate de tener Pillow instalado

# Configurar el logger

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

        # Crear una barra de menú
        self.menu_bar = Menu(root)
        self.root.config(menu=self.menu_bar)

        # Agregar un menú de archivo
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Importar archivo Excel", command=self.load_file)
        self.menu_bar.add_cascade(label="Archivo", menu=file_menu)

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
            root, text="Generar Imágenes", command=self.generate_images
        )
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
        
        self.tipo_carnet_combobox.current(0)  # Establecer el valor predeterminado
        self.tipo_carnet_combobox.pack(pady=5, anchor="w", padx=10)

        # Instancia del generador de imágenes
        self.image_generator = ImageGenerator()

    def open_entry_window(self, title, item_values=None):

        """Abre una ventana para ingresar o editar los detalles de un producto."""

        detail_window = tk.Toplevel(self.root)

        detail_window.title(title)


        # Crear variables para almacenar los valores editables

        edit_vars = [tk.StringVar(value=value) for value in (item_values or [""] * 6)]


        # Crear etiquetas y campos de entrada

        labels = ["Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "Ruta Imagen"]

        for i, label in enumerate(labels):

            tk.Label(detail_window, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')

            tk.Entry(detail_window, textvariable=edit_vars[i]).grid(row=i, column=1, padx=5, pady=5)


        # Label para mostrar la imagen

        self.image_display = tk.Label(detail_window, bd=2, relief="sunken")

        self.image_display.grid(row=len(labels), column=1, columnspan=2, pady=10)


        # Función para seleccionar la imagen

        def select_image():

            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])

            if file_path:

                edit_vars[5].set(file_path)

                img = Image.open(file_path)

                img.thumbnail((100, 100))

                img_tk = ImageTk.PhotoImage(img)

                self.image_display.config(image=img_tk)

                self.image_display.image = img_tk


        # Botón para seleccionar la imagen

        tk.Button(detail_window, text="Seleccionar Imagen", command=select_image).grid(row=len(labels), column=0, pady=5)


        # Botón para guardar nueva entrada o cambios

        action = "Guardar Nueva Entrada" if item_values is None else "Guardar Cambios"

        save_command = lambda: self.save_new_entry(edit_vars, detail_window) if item_values is None else self.save_changes(edit_vars, self.tree.selection()[0], detail_window)

        tk.Button(detail_window, text=action, command=save_command).grid(row=len(labels) + 2, column=0, columnspan=2, pady=5)


        # Cargar imagen si se está editando

        if item_values:

            self.load_image(item_values[5])

    def open_new_entry_window(self):

        """Abre una nueva ventana para ingresar los detalles de un nuevo producto."""

        self.open_entry_window("Nueva Entrada")

    def open_detail_window(self, event):

        """Abre una ventana para editar los detalles de la entrada seleccionada."""

        selected_item = self.tree.selection()

        if selected_item:

            item_values = self.tree.item(selected_item[0])["values"]

            if len(item_values) == 6:

                self.open_entry_window("Editar Trabajador", item_values)

            else:

                messagebox.showerror("Error", "Los datos seleccionados no son válidos.")

    def save_entry(self, edit_vars, detail_window, item_id=None):
        new_values = [var.get() for var in edit_vars]

        # Validación de campos vacíos
        if any(value.strip() == "" for value in new_values):
            messagebox.showerror("Error", "Todos los campos deben ser completados.")
            return

        # Validación de la cédula
        if not self.is_valid_cedula(new_values[2]):
            messagebox.showerror("Error", "La cédula debe contener solo números y tener 7 u 8 dígitos.")
            return

        # Validación de la existencia del archivo de imagen
        if not os.path.isfile(new_values[5]):
            messagebox.showerror("Error", "El archivo de imagen no existe.")
            return

        # Actualizar o agregar la entrada en el Treeview
        if item_id is not None:
            self.tree.item(item_id, values=new_values)  # Actualizar entrada existente
        else:
            self.tree.insert("", "end", values=new_values)  # Agregar nueva entrada

        detail_window.destroy()  # Cerrar la ventana

    def save_changes(self, edit_vars, item_id, detail_window):
        self.save_entry(edit_vars, detail_window, item_id)

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
                ]

                # Verificar que las columnas requeridas estén presentes
                if not all(col in self.df.columns for col in required_columns):
                    raise ValueError(
                        f"El Data Frame debe contener las columnas: {required_columns}"
                    )

                # Insertar los datos en el Treeview sin limpiar
                for index, row in self.df.iterrows():
                    # Crear una lista de valores, asegurando que Nombre, Apellidos y Cedula estén presentes
                    values = [
                        row.get("Nombre", ""),      # Obligatorio
                        row.get("Apellidos", ""),   # Obligatorio
                        row.get("Cedula", ""),      # Obligatorio
                        row.get("Adscrito", ""),    # Opcional
                        row.get("Cargo", ""),       # Opcional
                        ""                           # Campo vacío para la ruta de la imagen
                    ]
                    self.tree.insert("", "end", values=values)

            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def load_image(self, img_path):
        """Carga y muestra la imagen en el label."""    
        if os.path.isfile(img_path):    
            img = Image.open(img_path)  
            img.thumbnail((100, 100))   
            img_tk = ImageTk.PhotoImage(img)    
            self.image_display.config(image=img_tk) 
            self.image_display.image = img_tk

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


        total_generados = 0

        total_errores = 0

        errores = []


        for item in selected_items:

            data_row = self.tree.item(item)["values"]

            tipo_carnet = self.tipo_carnet_var.get()  # Obtener el tipo de carnet del combobox


            # Obtener la ruta de la imagen desde el data_row

            ruta_imagen = data_row[5]  # Suponiendo que la ruta de la imagen es el sexto elemento (índice 5)


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

                # Generar la imagen

                image_filename = self.image_generator.generate_image(

                    dict(zip(self.tree["columns"], data_row)), tipo_carnet, ruta_imagen

                )

                print(f"Imagen generada: {image_filename}")

                total_generados += 1  # Incrementar contador de generados


            except Exception as e:

                total_errores += 1  # Incrementar contador de errores

                errores.append(f"Error al generar imagen para {nombre} {apellidos} (Cédula: {cedula})")

                logging.error(f"No se pudo generar la imagen para {tipo_carnet}: {str(e)} - {nombre} {apellidos} (Cédula: {cedula})")


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


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()