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
                        "", "end", values=list(row) + [""]  # Agregar un campo vacío para la ruta de la imagen  
                    )  
 
            except Exception as e:  
                messagebox.showerror("Error", str(e))

    def open_detail_window(self, event):
        """Abre una nueva ventana con los detalles del producto seleccionado para editar."""    
        selected_item = self.tree.selection()   
        
        if not selected_item:   
            return  # No hay selección, no hacer nada
        
        item_values = self.tree.item(selected_item[0])["values"]    
        detail_window = tk.Toplevel(self.root)  
        detail_window.title("Editar Detalles del Producto") 
        # Crear variables para almacenar los valores editables  
        edit_vars = [tk.StringVar(value=value) for value in item_values]    
        # Crear etiquetas y campos de entrada para cada detalle 
        labels = ["Nombre", "Apellidos", "Cedula", "Adscrito", "Cargo", "Ruta Imagen"]  
        
        for i, label in enumerate(labels):  
            tk.Label(detail_window, text=label).pack(pady=5)    
            entry = tk.Entry(detail_window, textvariable=edit_vars[i])  
            entry.pack(pady=5)

        # Función para seleccionar la imagen    
        def select_image(): 
            file_path = filedialog.askopenfilename( 
                filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")] 
            )

            if file_path:   
                edit_vars[5].set(file_path)  # Actualizar la ruta de la imagen en el campo correspondiente  
        
        # Botón para seleccionar la imagen  
        image_button = tk.Button(detail_window, text="Seleccionar Imagen", command=select_image)    
        image_button.pack(pady=10)  
        
        # Función para guardar los cambios  
        def save_changes(): 
            new_values = [var.get() for var in edit_vars]   
            self.tree.item(selected_item[0], values=new_values)  # Actualizar el Treeview   
            detail_window.destroy()  # Cerrar la ventana de edición 
        
        # Botón para guardar cambios    
        save_button = tk.Button(detail_window, text="Guardar Cambios", command=save_changes)    
        save_button.pack(pady=10)   
        
        # Botón para cerrar la ventana sin guardar  
        close_button = tk.Button(detail_window, text="Cerrar", command=detail_window.destroy)   
        close_button.pack(pady=5)

    def generate_images(self):
        """Genera imágenes para todos los carnets seleccionados en el Treeview."""
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

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()