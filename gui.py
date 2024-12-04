import pandas as pd
import tkinter as tk
import os
from tkinter import filedialog, messagebox, Menu
from tkinter import ttk
from image_generator import ImageGenerator  # Asegúrate de tener la clase ImageGenerator implementada
from PIL import Image, ImageTk  # Asegúrate de tener Pillow instalado

class ImageGeneratorApp:
    def __init__(self, root):
        """Inicializa la aplicación de generación de carnets de imagen."""
        self.root = root
        self.root.title("Generador de Carnets de Imagen")

        # Crear una barra de menú
        self.menu_bar = Menu(root)
        self.root.config(menu=self.menu_bar)

        # Agregar un menú de archivo
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Abrir archivo Excel", command=self.load_file)
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
            columns=("Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "Ruta Imagen"),
            show="headings",
        )

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)

        self.tree.pack(pady=10, padx=10, fill="both", expand=True)

        # Asociar el evento de doble clic con el método open_detail_window
        self.tree.bind("<Double-1>", self.open_detail_window)

        # Botón para generar imágenes
        self.generate_button = tk.Button(
            root, text="Generar Imágenes", command=self.generate_images
        )
        self.generate_button.pack(pady=5, anchor="w", padx=10)

        # Botón para crear una nueva entrada
        self.new_entry_button = tk.Button(
            root, text="Nueva Entrada", command=self.open_new_entry_window
        )
        self.new_entry_button.pack(pady=5, anchor="w", padx=10)

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
        self.tipo_carnet_combobox.current(0)  # Establecer el valor predeterminado
        self.tipo_carnet_combobox.pack(pady=5, anchor="w", padx=10)

        self.image_generator = ImageGenerator()  # Instancia del generador de imágenes

    def open_new_entry_window(self):

        """Abre una nueva ventana para ingresar los detalles de un nuevo producto."""

        detail_window = tk.Toplevel(self.root)

        detail_window.title("Nueva Entrada")


        # Crear variables para almacenar los valores editables

        edit_vars = [tk.StringVar() for _ in range(6)]  # Seis campos para los datos


        # Crear etiquetas y campos de entrada para cada detalle

        labels = ["Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "Ruta Imagen"]


        for i, label in enumerate(labels):

            tk.Label(detail_window, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')

            entry = tk.Entry(detail_window, textvariable=edit_vars[i])

            entry.grid(row=i, column=1, padx=5, pady=5)


        # Label para mostrar la imagen

        self.image_display = tk.Label(detail_window)

        self.image_display.grid(row=len(labels), column=0, columnspan=2, pady=10)


        # Función para seleccionar la imagen

        def select_image():

            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])

            if file_path:

                edit_vars[5].set(file_path)  # Guardar la ruta de la imagen

                img = Image.open(file_path)

                img.thumbnail((100, 100))  # Cambiar el tamaño para mostrar

                img_tk = ImageTk.PhotoImage(img)

                self.image_display.config(image=img_tk)

                self.image_display.image = img_tk  # Mantener una referencia a la imagen


        # Botón para seleccionar la imagen

        select_image_button = tk.Button(detail_window, text="Seleccionar Imagen", command=select_image)

        select_image_button.grid(row=len(labels), column=1, pady=5)


        # Botón para guardar nueva entrada

        save_button = tk.Button(detail_window, text="Guardar Nueva Entrada", command=lambda: self.save_new_entry(edit_vars, detail_window))

        save_button.grid(row=len(labels) + 1, column=0, columnspan=2, pady=5)


    def save_new_entry(self, edit_vars, detail_window):

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


        # Agregar nueva entrada al Treeview

        img = Image.open(new_values[5])

        img.thumbnail((100, 100))  # Cambiar el tamaño para que se ajuste al Treeview

        img_tk = ImageTk.PhotoImage(img)


        # Aquí aseguramos que la ruta de la imagen se incluya en los valores

        self.tree.insert("", "end", values=new_values[:-1] + [new_values[5]], image=img_tk)  # Agregar nueva entrada al Treeview

        self.tree.image = img_tk  # Mantener una referencia a la imagen

        detail_window.destroy()  # Cerrar la ventana de nueva entrada


    def open_detail_window(self, event):
        """Abre una ventana para editar los detalles de la entrada seleccionada."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        detail_window = tk.Toplevel(self.root)
        detail_window.title("Editar Entrada")

        # Obtener los valores de la entrada seleccionada
        item_values = self.tree.item(selected_item[0])["values"]
        
        # Asegurarse de que item_values tenga la longitud esperada
        if len(item_values) != 6:  # Debe tener 6 elementos
            messagebox.showerror("Error", "Los datos seleccionados no son válidos.")
            return

        # Crear variables para almacenar los valores editables
        edit_vars = [tk.StringVar(value=value) for value in item_values]

        # Crear etiquetas y campos de entrada para cada detalle
        labels = ["Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "Ruta Imagen"]

        for i, label in enumerate(labels):
            tk.Label(detail_window, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            entry = tk.Entry(detail_window, textvariable=edit_vars[i])
            entry.grid(row=i, column=1, padx=5, pady=5)

        # Label para mostrar la imagen
        self.image_display = tk.Label(detail_window)
        self.image_display.grid(row=len(labels), column=0, columnspan=2, pady=10)

        # Cargar y mostrar la imagen seleccionada
        img_path = item_values[5]  # Obtener la ruta de la imagen
        if os.path.isfile(img_path):  # Verificar si la ruta es válida
            img = Image.open(img_path)
            img.thumbnail((100, 100))  # Cambiar el tamaño para mostrar
            img_tk = ImageTk.PhotoImage(img)
            self.image_display.config(image=img_tk)
            self.image_display.image = img_tk  # Mantener una referencia a la imagen

        # Función para seleccionar la imagen
        def select_image():
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
            if file_path:
                edit_vars[5].set(file_path)  # Guardar la ruta de la imagen
                img = Image.open(file_path)
                img.thumbnail((100, 100))  # Cambiar el tamaño para mostrar
                img_tk = ImageTk.PhotoImage(img)
                self.image_display.config(image=img_tk)
                self.image_display.image = img_tk  # Mantener una referencia a la imagen

        # Botón para seleccionar la imagen
        select_image_button = tk.Button(detail_window, text="Seleccionar Imagen", command=select_image)
        select_image_button.grid(row=len(labels), column=1, pady=5)

        # Botón para guardar cambios
        save_button = tk.Button(detail_window, text="Guardar Cambios", command=lambda: self.save_changes(edit_vars, selected_item[0], detail_window))
        save_button.grid(row=len(labels) + 1, column=0, columnspan=2, pady=5)
        
    def save_changes(self, edit_vars, item_id, detail_window):

        new_values = [var.get() for var in edit_vars]


        # Validación de campos vacíos

        if any(value.strip() == "" for value in new_values):

            messagebox.showerror("Error", "Todos los campos deben ser completados.")

            return


        # Validación de la existencia del archivo de imagen

        if not os.path.isfile(new_values[5]):

            messagebox.showerror("Error", "El archivo de imagen no existe.")

            return


        # Actualizar la entrada en el Treeview

        self.tree.item(item_id, values=new_values)

        detail_window.destroy()  # Cerrar la ventana de edición
        
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
                        f"El Data Frame debe contener las columnas: {required_columns}"
                    )

                # Limpiar el Treeview antes de cargar nuevos datos
                for i in self.tree.get_children():
                    self.tree.delete(i)

                # Insertar los datos en el Treeview
                for index, row in self.df.iterrows():
                    self.tree.insert(
                        "", "end", values=list(row) + [""]  # Agregar un campo vacío para la ruta de la imagen
                    )

            except Exception as e:
                messagebox.showerror("Error", str(e))

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

        for item in selected_items:
            data_row = self.tree.item(item)["values"]
            tipo_carnet = self.tipo_carnet_var.get()  # Obtener el tipo de carnet del combobox

            # Obtener la ruta de la imagen desde el data_row
            ruta_imagen = data_row[5]  # Suponiendo que la ruta de la imagen es el sexto elemento (índice 5)
            try:
                # Aquí puedes usar la ruta de la imagen como desees
                # Por ejemplo, podrías pasarla al generador de imágenes
                image_filename = self.image_generator.generate_image(
                    dict(zip(self.tree["columns"], data_row)), tipo_carnet, ruta_imagen
                )
                print(f"Imagen generada: {image_filename}")

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"No se pudo generar la imagen para {tipo_carnet}: {str(e)}",
                )

        messagebox.showinfo(
            "Éxito", "Todas las imágenes seleccionadas han sido generadas."
        )

    def is_valid_cedula(self, cedula):
        """Valida que la cédula contenga solo números y tenga 7 u 8 dígitos."""
        return cedula.isdigit() and len(cedula) in (7, 8)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()