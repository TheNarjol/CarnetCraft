import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, Menu
from tkinter import ttk
from image_generator import ImageGenerator  # Importar la clase de generación de imágenes

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
        # Botón para generar imágenes
        self.generate_button = tk.Button(
            root, text="Generar Imágenes", command=self.generate_images
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
        self.tipo_carnet_combobox.current(0)  # Establecer el valor predeterminado
        self.tipo_carnet_combobox.pack(pady=5, anchor="w", padx=10)

        self.image_generator = ImageGenerator()  # Instancia del generador de imágenes

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

    def generate_images(self):
        """Genera imágenes para todos los carnets seleccionados en el Tree view."""
        if self.df is None:
            messagebox.showwarning(
                "Advertencia", "Por favor, carga un archivo Excel primero."
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
            try:
                image_filename = self.image_generator.generate_image(
                    dict(zip(self.tree["columns"], data_row)), tipo_carnet
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

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()