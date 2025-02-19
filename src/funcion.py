import io
from PIL import Image

def convertir_imagen_a_binario(ruta_imagen):
    """
    Convierte una imagen a datos binarios.

    Parámetros:
    - ruta_imagen (str): Ruta de la imagen a convertir.

    Retorna:
    - bytes: Datos binarios de la imagen.
    """
    try:
        # Abre la imagen desde un archivo
        img = Image.open(ruta_imagen)

        # Convierte la imagen a datos binarios
        binary_data = io.BytesIO()
        img.save(binary_data, format='PNG')
        binary_data = binary_data.getvalue()

        return binary_data
    except Exception as e:
        print(f"Error al convertir la imagen a binario: {e}")
        return None

def crear_image_thumbnail_binarios(binarios):
        """
        Crea una imagen desde datos binarios utilizando PIL.

        Args:
            binarios (bytes): Datos binarios de la imagen.

        Returns:
            Image: Objeto de imagen de PIL.

        Raises:
            ValueError: Si los datos binarios están vacíos o no son válidos.
            Exception: Si ocurre un error al procesar la imagen.
        """
        try:
            # Verificar si los datos binarios están vacíos o no son válidos
            if not binarios:
                raise ValueError("Los datos binarios están vacíos o no son válidos.")

            # Convertir los datos binarios en una imagen usando PIL
            imagen = Image.open(io.BytesIO(binarios))

            return imagen

        except Exception as e:
            print(f"Error al crear la imagen desde binarios: {str(e)}")
            raise

def convertir_str_a_bytes(binary_str):
        """
        Convierte una cadena que contiene datos binarios en bytes.

        Args:
            binary_str (str): Cadena que contiene datos binarios.

        Returns:
            bytes: Datos binarios.
        """
        try:
            return binary_str.encode('latin1')  # Usar 'latin1' para preservar los bytes
        except Exception as e:
            print(f"Error al convertir la cadena a bytes: {str(e)}")
            raise

