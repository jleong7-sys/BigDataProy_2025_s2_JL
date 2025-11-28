import os
import zipfile
import requests
import json
import PyPDF2
from PIL import Image
import pytesseract
from typing import Dict, List, Optional
from werkzeug.utils import secure_filename
from datetime import datetime

class Funciones:
    @staticmethod
    def crear_carpeta(ruta: str) -> bool:
        """Crea una carpeta si no existe"""
        try:
            if not os.path.exists(ruta):
                os.makedirs(ruta)
            return True
        except Exception as e:
            print(f"Error al crear carpeta: {e}")
            return False
    
    @staticmethod
    def descomprimir_zip_local(ruta_file_zip: str, ruta_descomprimir: str) -> List[Dict]:
        """Descomprime un archivo ZIP y retorna info de archivos"""
        archivos = []
        try:
            with zipfile.ZipFile(ruta_file_zip, 'r') as zip_ref:
                # Verificar que el archivo ZIP no esté corrupto
                zip_ref.testzip()
                
                for file_info in zip_ref.namelist():
                    if not file_info.endswith('/'):
                        # Extraer carpeta padre
                        carpeta = os.path.dirname(file_info)
                        nombre_archivo = os.path.basename(file_info)
                        extension = os.path.splitext(nombre_archivo)[1].lower()
                        
                        # Solo procesar txt, pdf y json
                        if extension in ['.txt', '.pdf', '.json']:
                            # Extraer archivo
                            zip_ref.extract(file_info, ruta_descomprimir)
                            ruta_extraida = os.path.join(ruta_descomprimir, file_info)
                            
                            # Verificar que el archivo se extrajo correctamente
                            if os.path.exists(ruta_extraida):
                                archivos.append({
                                    'carpeta': carpeta if carpeta else 'raiz',
                                    'nombre': nombre_archivo,
                                    'ruta': ruta_extraida,
                                    'extension': extension,
                                    'tamaño': os.path.getsize(ruta_extraida)
                                })
                                print(f"✅ Archivo extraído: {nombre_archivo}")
                            else:
                                print(f"❌ Archivo no encontrado después de extraer: {ruta_extraida}")
                return archivos
        except zipfile.BadZipFile as e:
            print(f"Error: Archivo ZIP corrupto - {e}")
            return []
        except Exception as e:
            print(f"Error al descomprimir ZIP: {e}")
            return []
    
    @staticmethod
    def descargar_y_descomprimir_zip(url: str, carpeta_destino: str, tipoArchivo: str = '') -> List[Dict]:
        """Descarga y descomprime un ZIP desde URL"""
        try:
            if not Funciones.crear_carpeta(carpeta_destino):
                return []
            
            # Descargar archivo con timeout
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()  # Lanza excepción para códigos de error HTTP
            
            zip_path = os.path.join(carpeta_destino, 'temp.zip')
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Descomprimir
            archivos = Funciones.descomprimir_zip_local(zip_path, carpeta_destino)
            
            # Eliminar ZIP temporal
            try:
                os.remove(zip_path)
            except OSError as e:
                print(f"Advertencia: No se pudo eliminar archivo temporal: {e}")
            
            return archivos
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al descargar: {e}")
            return []
        except Exception as e:
            print(f"Error al descargar y descomprimir: {e}")
            return []
    
    @staticmethod
    def allowed_file(filename: str, extensions: List[str]) -> bool:
        """Verifica si un archivo tiene extensión permitida"""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in extensions
    
    @staticmethod
    def borrar_contenido_carpeta(ruta: str) -> bool:
        """
        Borra el contenido de una carpeta sin eliminar la carpeta misma
        """
        try:
            if not os.path.exists(ruta):
                return True
            
            if not os.path.isdir(ruta):
                return False
            
            for item in os.listdir(ruta):
                item_path = os.path.join(ruta, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        import shutil
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"Error al eliminar {item_path}: {e}")
                    return False
            
            return True
        except Exception as e:
            print(f"Error al borrar contenido de carpeta: {e}")
            return False
    
    @staticmethod
    def extraer_texto_pdf(ruta_pdf: str) -> str:
        """
        Extrae texto de un archivo PDF
        """
        try:
            if not os.path.exists(ruta_pdf):
                print(f"Error: Archivo PDF no encontrado - {ruta_pdf}")
                return ""
            
            texto = ""
            with open(ruta_pdf, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Verificar si el PDF está encriptado
                if pdf_reader.is_encrypted:
                    print(f"Advertencia: PDF encriptado - {ruta_pdf}")
                    return ""
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        texto += page_text + "\n"
            
            return texto.strip()
        except PyPDF2.PdfReadError as e:
            print(f"Error al leer PDF {ruta_pdf}: {e}")
            return ""
        except Exception as e:
            print(f"Error al extraer texto del PDF {ruta_pdf}: {e}")
            return ""
    
    @staticmethod
    def extraer_texto_pdf_ocr(ruta_pdf: str) -> str:
        """
        Extrae texto de un PDF usando OCR (útil para PDFs escaneados)
        """
        try:
            # Verificar dependencias
            try:
                from pdf2image import convert_from_path
            except ImportError:
                print("Error: pdf2image no está instalado. Instala con: pip install pdf2image")
                return ""
            
            if not os.path.exists(ruta_pdf):
                print(f"Error: Archivo PDF no encontrado - {ruta_pdf}")
                return ""
            
            # Convertir PDF a imágenes
            images = convert_from_path(ruta_pdf)
            
            texto = ""
            for i, image in enumerate(images):
                # Aplicar OCR a cada página
                page_text = pytesseract.image_to_string(image, lang='spa')
                if page_text.strip():
                    texto += f"--- Página {i+1} ---\n{page_text}\n"
            
            return texto.strip()
        except Exception as e:
            print(f"Error al extraer texto con OCR del PDF {ruta_pdf}: {e}")
            return ""
    
    @staticmethod
    def listar_archivos_json(ruta_carpeta: str) -> List[Dict]:
        """
        Lista todos los archivos JSON en una carpeta
        """
        archivos_json = []
        try:
            if not os.path.exists(ruta_carpeta):
                print(f"❌ Carpeta no existe: {ruta_carpeta}")
                return []
            
            print(f"📁 Buscando archivos JSON en: {ruta_carpeta}")
            
            for archivo in os.listdir(ruta_carpeta):
                if archivo.lower().endswith('.json'):
                    ruta_completa = os.path.join(ruta_carpeta, archivo)
                    if os.path.isfile(ruta_completa):
                        archivos_json.append({
                            'nombre': archivo,
                            'ruta': ruta_completa,
                            'tamaño': os.path.getsize(ruta_completa)
                        })
                        print(f"📄 Encontrado: {archivo}")
            
            print(f"✅ Total archivos JSON encontrados: {len(archivos_json)}")
            return archivos_json
        except Exception as e:
            print(f"❌ Error al listar archivos JSON: {e}")
            return []
    
    
    @staticmethod
    def listar_archivos_carpeta(ruta_carpeta: str, extensiones: Optional[List[str]] = None) -> List[Dict]:
        """
        Lista archivos en una carpeta con extensiones específicas
        """
        archivos = []
        try:
            if not os.path.exists(ruta_carpeta):
                return []
            
            for archivo in os.listdir(ruta_carpeta):
                ruta_completa = os.path.join(ruta_carpeta, archivo)
                if os.path.isfile(ruta_completa):
                    extension = os.path.splitext(archivo)[1].lower().replace('.', '')
                    
                    if extensiones is None or extension in [ext.lower().replace('.', '') for ext in extensiones]:
                        archivos.append({
                            'nombre': archivo,
                            'ruta': ruta_completa,
                            'extension': extension,
                            'tamaño': os.path.getsize(ruta_completa),
                            'fecha_modificacion': os.path.getmtime(ruta_completa)
                        })
            
            return archivos
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            return []
    
    @staticmethod
    def leer_json(ruta_json: str) -> Dict:
        """
        Lee un archivo JSON y retorna su contenido
        """
        try:
            if not os.path.exists(ruta_json):
                print(f"Error: Archivo JSON no encontrado - {ruta_json}")
                return {}
            
            with open(ruta_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: JSON malformado en {ruta_json}: {e}")
            return {}
        except UnicodeDecodeError as e:
            print(f"Error de codificación en {ruta_json}: {e}")
            return {}
        except Exception as e:
            print(f"Error al leer JSON {ruta_json}: {e}")
            return {}
    
    @staticmethod
    def guardar_json(ruta_json: str, datos: Dict) -> bool:
        """
        Guarda datos en un archivo JSON
        """
        try:
            # Crear directorio si no existe
            directorio = os.path.dirname(ruta_json)
            if directorio and not Funciones.crear_carpeta(directorio):
                return False
            
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar JSON: {e}")
            return False
    
    @staticmethod
    def leer_archivo_texto(ruta_archivo: str) -> str:
        """
        Lee el contenido de un archivo de texto
        """
        try:
            if not os.path.exists(ruta_archivo):
                return ""
            
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except UnicodeDecodeError:
            # Intentar con otra codificación si UTF-8 falla
            try:
                with open(ruta_archivo, 'r', encoding='latin-1') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Error de codificación al leer {ruta_archivo}: {e}")
                return ""
        except Exception as e:
            print(f"Error al leer archivo de texto {ruta_archivo}: {e}")
            return ""