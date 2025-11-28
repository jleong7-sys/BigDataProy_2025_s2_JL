import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin
import re

class RottenTomatoesScraper:
    def __init__(self):
        self.base_url = "https://editorial.rottentomatoes.com"
        self.start_url = "https://editorial.rottentomatoes.com/guide/best-new-movies/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.movies_data = []
        
    def get_soup(self, url):
        """Obtiene el contenido HTML de una URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error al obtener {url}: {e}")
            return None
    
    def extract_movie_data(self, movie_div):
        """Extrae los datos de una película individual"""
        try:
            movie_data = {}
            
            # Extraer título
            title_element = movie_div.find('h2')
            if title_element:
                movie_data['title'] = title_element.get_text(strip=True)
            
            # Extraer año
            year_element = movie_div.find('span', class_='subtle start-year')
            if year_element:
                movie_data['year'] = year_element.get_text(strip=True).strip('()')
            
            # Extraer score de Tomatometer
            tomatometer_element = movie_div.find('span', class_='tMeterScore')
            if tomatometer_element:
                movie_data['tomatometer_score'] = tomatometer_element.get_text(strip=True)
            
            # Extraer información de consenso
            consensus_element = movie_div.find('div', class_='consensus')
            if consensus_element:
                movie_data['consensus'] = consensus_element.get_text(strip=True)
            
            # Extraer información de directores y reparto
            info_elements = movie_div.find_all('div', class_='info')
            for info in info_elements:
                label = info.find('b')
                if label:
                    label_text = label.get_text(strip=True).lower().replace(':', '')
                    value = info.get_text().replace(label.get_text(), '').strip()
                    movie_data[label_text] = value
            
            # Extraer imagen
            image_element = movie_div.find('img')
            if image_element and 'src' in image_element.attrs:
                movie_data['image_url'] = image_element['src']
            
            # Extraer enlace a la página de la película
            link_element = movie_div.find('a', href=True)
            if link_element:
                movie_data['url'] = urljoin(self.base_url, link_element['href'])
            
            # Extraer posición en la lista
            position_element = movie_div.find('span', class_='countdown-index')
            if position_element:
                movie_data['position'] = position_element.get_text(strip=True).replace('#', '')
            
            return movie_data
            
        except Exception as e:
            print(f"Error extrayendo datos de película: {e}")
            return None
    
    def scrape_movies(self):
        """Scraping principal de todas las películas"""
        print("🔍 Iniciando scraping de Rotten Tomatoes...")
        
        soup = self.get_soup(self.start_url)
        if not soup:
            return False
        
        # Encontrar todos los divs de películas
        movie_divs = soup.find_all('div', class_='row countdown-item')
        
        print(f"📊 Encontradas {len(movie_divs)} películas en la página principal")
        
        for i, movie_div in enumerate(movie_divs, 1):
            print(f"🎬 Procesando película {i}/{len(movie_divs)}...")
            
            movie_data = self.extract_movie_data(movie_div)
            if movie_data:
                self.movies_data.append(movie_data)
                print(f"✅ {movie_data.get('title', 'Sin título')}")
            else:
                print(f"❌ Error procesando película {i}")
            
            # Pausa para no saturar el servidor
            time.sleep(0.5)
        
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
                title = movie.get('title', f'movie_{i}')
                # Limpiar el título para el nombre de archivo
                safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
                safe_title = safe_title.replace(' ', '_').lower()
                filename = f"{i:03d}_{safe_title}.json"
                filepath = os.path.join(output_dir, filename)
                
                # Guardar archivo JSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(movie, f, indent=2, ensure_ascii=False)
                
                saved_count += 1
                print(f"💾 Guardado: {filename}")
                
            except Exception as e:
                print(f"❌ Error guardando {filename}: {e}")
        
        return saved_count
    
    def save_combined_json(self, output_dir):
        """Guarda todas las películas en un archivo JSON combinado"""
        combined_file = os.path.join(output_dir, "all_movies_combined.json")
        try:
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "total_movies": len(self.movies_data),
                    "scraped_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "movies": self.movies_data
                }, f, indent=2, ensure_ascii=False)
            print(f"📚 Archivo combinado guardado: {combined_file}")
            return True
        except Exception as e:
            print(f"❌ Error guardando archivo combinado: {e}")
            return False
    
    def run(self):
        """Ejecuta el scraping completo"""
        print("🎯 Rotten Tomatoes Scraper")
        print("=" * 50)
        
        # Realizar scraping
        if self.scrape_movies():
            print(f"\n✅ Scraping completado. Total de películas: {len(self.movies_data)}")
            
            # Definir directorio de salida
            output_dir = "D:/UCENTRAL/IISemestre/BD/PROYECTO/RT"
            
            # Guardar archivos individuales
            saved_count = self.save_individual_json_files(output_dir)
            print(f"\n📁 Archivos individuales guardados: {saved_count}/{len(self.movies_data)}")
            
            # Guardar archivo combinado
            self.save_combined_json(output_dir)
            
            # Mostrar resumen
            print("\n" + "=" * 50)
            print("📊 RESUMEN FINAL")
            print("=" * 50)
            print(f"🎬 Películas procesadas: {len(self.movies_data)}")
            print(f"💾 Archivos JSON guardados: {saved_count}")
            print(f"📂 Ubicación: {os.path.abspath(output_dir)}")
            
            # Mostrar algunas películas como ejemplo
            if self.movies_data:
                print("\n🎭 Primeras 5 películas:")
                for i, movie in enumerate(self.movies_data[:5], 1):
                    print(f"  {i}. {movie.get('title', 'Sin título')} ({movie.get('year', 'N/A')}) - {movie.get('tomatometer_score', 'N/A')}")
            
        else:
            print("❌ Error en el scraping")

def main():
    """Función principal"""
    scraper = RottenTomatoesScraper()
    scraper.run()

if __name__ == "__main__":
    main()