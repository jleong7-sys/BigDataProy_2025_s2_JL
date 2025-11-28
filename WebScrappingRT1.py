import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin
import re
from deep_translator import GoogleTranslator

class RottenTomatoesScraperES:
    def __init__(self):
        self.base_url = "https://editorial.rottentomatoes.com"
        self.start_url = "https://editorial.rottentomatoes.com/guide/best-new-movies/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.movies_data = []
        self.translator = GoogleTranslator(source='auto', target='es')
        
    def traducir_texto(self, texto):
        """Traduce texto al español"""
        try:
            if texto and texto.strip():
                texto = texto[:4500]
                return self.translator.translate(texto)
            return texto
        except Exception as e:
            print(f"⚠️ Error en traducción: {e}")
            return texto
    
    def get_soup(self, url):
        """Obtiene el contenido HTML de una URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error al obtener {url}: {e}")
            return None
    
    def extract_section_text(self, movie_div, section_name):
        """Extrae texto de una sección específica como Critics Consensus, Synopsis, etc."""
        try:
            # Buscar todos los elementos de texto que podrían contener la sección
            all_text_elements = movie_div.find_all(string=True)
            
            for text_element in all_text_elements:
                text = text_element.strip()
                if section_name.lower() in text.lower():
                    # Encontramos la sección, ahora obtener el texto completo del contenedor
                    parent = text_element.parent
                    if parent:
                        full_text = parent.get_text(strip=True)
                        # Extraer solo el contenido después del nombre de la sección
                        pattern = rf"{section_name}[:\s]*(.+)"
                        match = re.search(pattern, full_text, re.IGNORECASE)
                        if match:
                            return match.group(1).strip()
            
            return None
        except Exception as e:
            print(f"Error extrayendo {section_name}: {e}")
            return None
    
    def extract_movie_data(self, movie_div):
        """Extrae los datos completos de una película individual en español"""
        try:
            movie_data = {}
            
            # Extraer posición (#1, #2, etc.)
            position_element = movie_div.find('span', class_='countdown-index')
            if position_element:
                position = position_element.get_text(strip=True)
                movie_data['posicion'] = position
                print(f"   🎬 Procesando {position}")
            
            # Extraer título (limpiar año si está incluido)
            title_element = movie_div.find('h2')
            if title_element:
                title_text = title_element.get_text(strip=True)
                # Remover el año si está en el título
                title_clean = re.sub(r'\s*\(\d{4}\)\s*\d+%$', '', title_text)
                movie_data['titulo'] = self.traducir_texto(title_clean)
            
            # Extraer score de Tomatometer
            tomatometer_element = movie_div.find('span', class_='tMeterScore')
            if tomatometer_element:
                score_text = tomatometer_element.get_text(strip=True)
                movie_data['puntuacion_tomatometro'] = score_text
                movie_data['icono_tomatometro'] = "Icono del tomatómetro"
            
            # EXTRAER CRITICS CONSENSUS
            critics_consensus = self.extract_section_text(movie_div, "Critics Consensus")
            if critics_consensus:
                movie_data['critics_consensus'] = self.traducir_texto(critics_consensus)
                print(f"   ✅ Critics Consensus encontrado")
            else:
                print(f"   ❌ Critics Consensus NO encontrado")
            
            # EXTRAER SYNOPSIS
            synopsis = self.extract_section_text(movie_div, "Synopsis")
            if synopsis:
                movie_data['synopsis'] = self.traducir_texto(synopsis)
                print(f"   ✅ Synopsis encontrado")
            else:
                print(f"   ❌ Synopsis NO encontrado")
            
            # EXTRAER STARRING
            starring = self.extract_section_text(movie_div, "Starring")
            if starring:
                movie_data['starring'] = self.traducir_texto(starring)
                print(f"   ✅ Starring encontrado")
            else:
                print(f"   ❌ Starring NO encontrado")
            
            # EXTRAER DIRECTED BY
            directed_by = self.extract_section_text(movie_div, "Directed By")
            if directed_by:
                movie_data['directed_by'] = self.traducir_texto(directed_by)
                print(f"   ✅ Directed By encontrado")
            else:
                print(f"   ❌ Directed By NO encontrado")
            
            # Si no encontramos la información con el método anterior, intentemos con búsqueda más agresiva
            if not all([critics_consensus, synopsis, starring, directed_by]):
                self.extract_using_alternative_method(movie_div, movie_data)
            
            # Extraer imagen
            image_element = movie_div.find('img')
            if image_element and 'src' in image_element.attrs:
                movie_data['url_imagen'] = image_element['src']
                movie_data['alt_imagen'] = image_element.get('alt', '')
            
            # Extraer enlace a la página de la película
            link_element = movie_div.find('a', href=True)
            if link_element:
                movie_url = urljoin(self.base_url, link_element['href'])
                movie_data['url_pelicula'] = movie_url
            
            # Información de scraping
            movie_data['fecha_extraccion'] = time.strftime("%Y-%m-%d %H:%M:%S")
            movie_data['fuente'] = "Rotten Tomatoes - Guía de Mejores Nuevas Películas"
            
            return movie_data
            
        except Exception as e:
            print(f"Error extrayendo datos de película: {e}")
            return None
    
    def extract_using_alternative_method(self, movie_div, movie_data):
        """Método alternativo para extraer información si el principal falla"""
        try:
            # Buscar todos los elementos div dentro del contenedor de la película
            info_divs = movie_div.find_all('div', class_=lambda x: x != 'row countdown-item')
            
            for div in info_divs:
                text = div.get_text(strip=True)
                
                # Critics Consensus
                if 'Critics Consensus:' in text and 'critics_consensus' not in movie_data:
                    consensus = text.split('Critics Consensus:')[1].strip()
                    movie_data['critics_consensus'] = self.traducir_texto(consensus)
                    print(f"   ✅ Critics Consensus (alternativo) encontrado")
                
                # Synopsis
                elif 'Synopsis:' in text and 'synopsis' not in movie_data:
                    synopsis_text = text.split('Synopsis:')[1].strip()
                    movie_data['synopsis'] = self.traducir_texto(synopsis_text)
                    print(f"   ✅ Synopsis (alternativo) encontrado")
                
                # Starring
                elif 'Starring:' in text and 'starring' not in movie_data:
                    starring_text = text.split('Starring:')[1].strip()
                    movie_data['starring'] = self.traducir_texto(starring_text)
                    print(f"   ✅ Starring (alternativo) encontrado")
                
                # Directed By
                elif 'Directed By:' in text and 'directed_by' not in movie_data:
                    directed_text = text.split('Directed By:')[1].strip()
                    movie_data['directed_by'] = self.traducir_texto(directed_text)
                    print(f"   ✅ Directed By (alternativo) encontrado")
                    
        except Exception as e:
            print(f"Error en método alternativo: {e}")
    
    def scrape_all_movies(self):
        """Scraping principal de todas las películas"""
        print("🔍 Iniciando scraping de Rotten Tomatoes...")
        print("🌐 Traduciendo contenido al español...")
        
        soup = self.get_soup(self.start_url)
        if not soup:
            return False
        
        # Encontrar todos los divs de películas
        movie_divs = soup.find_all('div', class_='row countdown-item')
        
        print(f"📊 Encontradas {len(movie_divs)} películas en la página principal")
        
        total_movies = len(movie_divs)
        for i, movie_div in enumerate(movie_divs, 1):
            position = movie_div.find('span', class_='countdown-index')
            pos_text = position.get_text(strip=True) if position else f"{i}"
            print(f"\n[{i}/{total_movies}] Procesando película {pos_text}...")
            
            movie_data = self.extract_movie_data(movie_div)
            if movie_data:
                self.movies_data.append(movie_data)
                titulo = movie_data.get('titulo', 'Sin título')
                puntuacion = movie_data.get('puntuacion_tomatometro', 'N/A')
                
                # Mostrar resumen de lo extraído
                extracted = []
                if movie_data.get('critics_consensus'):
                    extracted.append("Consensus")
                if movie_data.get('synopsis'):
                    extracted.append("Synopsis")
                if movie_data.get('starring'):
                    extracted.append("Starring")
                if movie_data.get('directed_by'):
                    extracted.append("Directed")
                
                info_str = " + ".join(extracted) if extracted else "Solo info básica"
                print(f"✅ {titulo} - {puntuacion} [{info_str}]")
            else:
                print(f"❌ Error procesando película {i}")
            
            # Pausa para no saturar el servidor
            if i < total_movies:
                time.sleep(1)
        
        return True
    
    def save_individual_json_files(self, output_dir):
        """Guarda cada película en un archivo JSON individual"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Carpeta creada: {output_dir}")
        
        saved_count = 0
        for i, movie in enumerate(self.movies_data, 1):
            try:
                # Crear nombre de archivo seguro
                titulo = movie.get('titulo', f'pelicula_{i}')
                safe_title = re.sub(r'[<>:"/\\|?*]', '', titulo)
                safe_title = re.sub(r'\s+', '_', safe_title)
                safe_title = safe_title.lower()[:50]
                
                posicion = movie.get('posicion', f'{i:03d}')
                filename = f"{posicion}_{safe_title}.json"
                filepath = os.path.join(output_dir, filename)
                
                # Guardar archivo JSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(movie, f, indent=2, ensure_ascii=False)
                
                saved_count += 1
                print(f"💾 {filename}")
                
            except Exception as e:
                print(f"❌ Error guardando archivo {i}: {e}")
        
        return saved_count
    
    def save_combined_json(self, output_dir):
        """Guarda todas las películas en un archivo JSON combinado"""
        combined_data = {
            "metadatos": {
                "total_peliculas": len(self.movies_data),
                "fecha_extraccion": time.strftime("%Y-%m-%d %H:%M:%S"),
                "fuente": "Rotten Tomatoes - Guía de Mejores Nuevas Películas",
                "idioma": "español"
            },
            "peliculas": self.movies_data
        }
        
        combined_file = os.path.join(output_dir, "todas_las_peliculas.json")
        try:
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)
            print(f"📚 Archivo combinado guardado: {combined_file}")
            return True
        except Exception as e:
            print(f"❌ Error guardando archivo combinado: {e}")
            return False
    
    def run(self):
        """Ejecuta el scraping completo"""
        print("🎯 Rotten Tomatoes Scraper - Versión Español")
        print("=" * 60)
        
        start_time = time.time()
        
        # Realizar scraping
        if self.scrape_all_movies():
            elapsed_time = time.time() - start_time
            
            print(f"\n✅ Scraping completado. Total de películas: {len(self.movies_data)}")
            print("💾 Guardando archivos...")
            
            # Definir directorio de salida
            output_dir = "D:/UCENTRAL/IISemestre/BD/PROYECTO/RT"
            
            # Guardar archivos individuales
            saved_count = self.save_individual_json_files(output_dir)
            print(f"\n📁 Archivos individuales guardados: {saved_count}/{len(self.movies_data)}")
            
            # Guardar archivo combinado
            self.save_combined_json(output_dir)
            
            # Mostrar resumen final
            print("\n" + "=" * 60)
            print("🎉 SCRAPING COMPLETADO")
            print("=" * 60)
            print(f"🎬 Total películas procesadas: {len(self.movies_data)}")
            print(f"💾 Archivos guardados: {saved_count}")
            print(f"⏱️  Tiempo: {elapsed_time:.2f} segundos")
            
            # Mostrar ejemplo detallado
            if self.movies_data:
                primera = self.movies_data[0]
                print(f"\n🎭 EJEMPLO COMPLETO:")
                print(f"Posición: {primera.get('posicion')}")
                print(f"Título: {primera.get('titulo')}")
                print(f"Tomatómetro: {primera.get('puntuacion_tomatometro')}")
                if primera.get('critics_consensus'):
                    print(f"Critics Consensus: {primera.get('critics_consensus')}")
                if primera.get('synopsis'):
                    print(f"Synopsis: {primera.get('synopsis')}")
                if primera.get('starring'):
                    print(f"Starring: {primera.get('starring')}")
                if primera.get('directed_by'):
                    print(f"Directed By: {primera.get('directed_by')}")
            
        else:
            print("❌ Error en el scraping")

def main():
    """Función principal"""
    try:
        import deep_translator
    except ImportError:
        print("📦 Instalando dependencia de traducción...")
        os.system("pip install deep-translator")
        import deep_translator
    
    scraper = RottenTomatoesScraperES()
    scraper.run()

if __name__ == "__main__":
    main()