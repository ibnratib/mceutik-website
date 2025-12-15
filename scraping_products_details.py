import requests
from bs4 import BeautifulSoup, Comment
import json
import re
from urllib.parse import urljoin
from typing import List, Dict, Optional
import hashlib

class DoppelherzScraper:
    def __init__(self):
        self.base_url = "https://www.doppelherz.ma"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def generate_id(self, url: str) -> str:
        """Génère un ID unique basé sur l'URL du produit"""
        return hashlib.md5(url.encode()).hexdigest()[:12]
    
    def extract_product_slug(self, url: str) -> str:
        """Extrait le slug du produit depuis l'URL"""
        return url.rstrip('/').split('/')[-1]
    
    def get_full_image_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extrait toutes les images principales du produit (pas celles dans la description)"""
        images = []
        
        # Chercher les images dans la galerie principale (les grandes images 812x812)
        img_tags = soup.select('img[src*="812x812"]')
        
        for img in img_tags:
            src = img.get('src', '')
            if src and '812x812' in src:
                full_url = urljoin(self.base_url, src)
                if full_url not in images:
                    images.append(full_url)
        
        return images
    
    def extract_product_highlights(self, soup: BeautifulSoup) -> List[str]:
        """Extrait les points forts du produit (à droite des images)"""
        highlights = []
        
        # Chercher la section avec les points clés (généralement des listes avec des icônes)
        # Ces éléments sont souvent dans la zone produit principale
        product_section = soup.select_one('.product-detail, .product-info, div[class*="product"]')
        
        if product_section:
            # Chercher les listes à puces dans cette section
            lists = product_section.select('ul')
            
            for ul in lists:
                # Vérifier si c'est bien une liste de caractéristiques produit
                # (pas un menu de navigation)
                if 'menu' not in ul.get('class', []) and 'nav' not in ul.get('class', []):
                    for li in ul.select('li'):
                        text = li.get_text(strip=True)
                        # Filtrer les éléments vides ou trop courts
                        if text and len(text) > 15 and not text.startswith('http'):
                            highlights.append(text)
                    
                    # Si on a trouvé des highlights, on arrête
                    if highlights:
                        break
        
        # Alternative: chercher directement les éléments avec icônes circulaires
        if not highlights:
            icon_items = soup.select('div[class*="icon"] + p, span[class*="icon"] + p')
            for item in icon_items:
                text = item.get_text(strip=True)
                if text and len(text) > 15:
                    highlights.append(text)
        
        return highlights
    
    def extract_attributes(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrait les attributs (icônes) du produit"""
        attributes = []
        
        attr_containers = soup.select('div[class*="attribute"], span[class*="attribute"]')
        for attr in attr_containers:
            img = attr.select_one('img')
            text = attr.get_text(strip=True)
            
            if img and text:
                attributes.append({
                    'icon': urljoin(self.base_url, img.get('src', '')),
                    'label': text
                })
        
        return attributes
    
    def clean_html_content(self, html: str) -> str:
        """Nettoie le contenu HTML"""
        if not html:
            return ""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Supprimer les commentaires HTML
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Supprimer les scripts et styles
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        return str(soup).strip()
    
    def extract_html_content(self, element) -> str:
        """Extrait le contenu HTML en préservant les balises importantes"""
        if not element:
            return ""
        
        # Convertir en string HTML
        html = str(element)
        
        # Supprimer les attributs de classe/style inutiles mais garder la structure
        soup = BeautifulSoup(html, 'html.parser')
        
        # Supprimer les commentaires
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Garder uniquement les balises importantes
        allowed_tags = ['p', 'strong', 'b', 'em', 'i', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br']
        
        for tag in soup.find_all():
            if tag.name not in allowed_tags:
                tag.unwrap()
            else:
                # Nettoyer les attributs
                tag.attrs = {}
        
        return str(soup).strip()
    
    def extract_composition_table(self, soup: BeautifulSoup) -> Optional[List[Dict]]:
        """Extrait le tableau de composition"""
        table = soup.select_one('table')
        if not table:
            return None
        
        composition = []
        rows = table.select('tr')[1:]  # Skip header
        
        for row in rows:
            cells = row.select('td')
            if len(cells) >= 2:
                composition.append({
                    'ingredient': cells[0].get_text(strip=True),
                    'quantity': cells[1].get_text(strip=True),
                    'vnr': cells[2].get_text(strip=True) if len(cells) > 2 else ''
                })
        
        return composition
    
    def scrape_product(self, product_url: str) -> Dict:
        """Scrape un produit individuel"""
        print(f"Scraping: {product_url}")
        
        response = requests.get(product_url, headers=self.headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraction des données
        product_slug = self.extract_product_slug(product_url)
        product_id = self.generate_id(product_url)
        
        # Titre et ligne de produit
        title_element = soup.select_one('h1')
        title = title_element.get_text(strip=True) if title_element else ""
        
        product_line = soup.select_one('h1 a')
        product_line_text = product_line.get_text(strip=True) if product_line else ""
        
        # Sous-titre
        subtitle = ""
        subtitle_elem = soup.select_one('h1 + p, .product-subtitle')
        if subtitle_elem:
            subtitle = subtitle_elem.get_text(strip=True)
        
        # Images principales
        images = self.get_full_image_urls(soup)
        
        # Attributs (icônes)
        attributes = self.extract_attributes(soup)
        
        # Points forts du produit (à droite des images)
        product_highlights = self.extract_product_highlights(soup)
        
        # Description complète (sections d'information)
        description_sections = []
        info_sections = soup.select('div[id*="tab-content"] h2, div[id*="tab-content"] > div')
        
        current_section = None
        for elem in info_sections:
            if elem.name == 'h2':
                if current_section:
                    description_sections.append(current_section)
                current_section = {
                    'title': elem.get_text(strip=True),
                    'content': ''
                }
            elif current_section:
                # Extraire le contenu suivant le h2
                content = self.extract_html_content(elem)
                if content:
                    current_section['content'] += content
        
        if current_section:
            description_sections.append(current_section)
        
        # Nettoyer les sections de description
        for section in description_sections:
            section['content'] = self.clean_html_content(section['content'])
        
        # Composition
        composition = self.extract_composition_table(soup)
        
        # Conseil d'utilisation
        usage_advice = ""
        usage_section = soup.select_one('h2:-soup-contains("Conseil d\'utilisation"), h3:-soup-contains("Conseil d\'utilisation")')
        if usage_section:
            next_elem = usage_section.find_next_sibling()
            if next_elem:
                usage_advice = self.clean_html_content(self.extract_html_content(next_elem))
        
        # Ingrédients
        ingredients = ""
        ingredients_section = soup.select_one('h2:-soup-contains("Ingrédients"), h3:-soup-contains("Ingrédients")')
        if ingredients_section:
            next_elem = ingredients_section.find_next_sibling()
            if next_elem:
                ingredients = self.clean_html_content(next_elem.get_text(strip=True))
        
        # Remarques
        remarks = ""
        remarks_section = soup.select_one('h2:-soup-contains("Remarques"), h3:-soup-contains("Remarques")')
        if remarks_section:
            next_elem = remarks_section.find_next_sibling()
            if next_elem:
                remarks = self.clean_html_content(self.extract_html_content(next_elem))
        
        # GTIN / Code-barres
        gtin = ""
        gtin_elem = soup.select_one('p:-soup-contains("GTIN")')
        if gtin_elem:
            gtin = gtin_elem.get_text(strip=True).replace('GTIN:', '').strip()
        
        # Package info
        package_info = []
        package_elems = soup.select('ul li:-soup-contains("gélules"), ul li:-soup-contains("comprimés"), ul li:-soup-contains("capsules")')
        for elem in package_elems:
            package_info.append(elem.get_text(strip=True))
        
        return {
            'id': product_id,
            'url_slug': product_slug,
            'full_url': product_url,
            'title': title,
            'product_line': product_line_text,
            'subtitle': subtitle,
            'images': images,
            'attributes': attributes,
            'product_highlights': product_highlights,
            'package_info': package_info,
            'description_sections': description_sections,
            'composition': composition,
            'usage_advice': usage_advice,
            'ingredients': ingredients,
            'remarks': remarks,
            'gtin': gtin
        }
    
    def scrape_products_list(self, category_url: str) -> List[str]:
        """Récupère la liste des URLs de produits depuis une page de catégorie"""
        response = requests.get(category_url, headers=self.headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        product_urls = []
        product_links = soup.select('a[href*="/produits/doppelherz"]')
        
        for link in product_links:
            href = link.get('href')
            if href and '/produits/doppelherz-' in href and href not in product_urls:
                full_url = urljoin(self.base_url, href)
                product_urls.append(full_url)
        
        return product_urls
    
    def scrape_all_products(self, product_urls: List[str], output_file: str = 'products.json'):
        """Scrape tous les produits et sauvegarde en JSON"""
        all_products = []
        
        for url in product_urls:
            try:
                product = self.scrape_product(url)
                all_products.append(product)
                print(f"✓ Produit scraped: {product['title']}")
            except Exception as e:
                print(f"✗ Erreur pour {url}: {str(e)}")
        
        # Sauvegarder en JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)
        
        print(f"\n{len(all_products)} produits sauvegardés dans {output_file}")
        return all_products


# # Exemple d'utilisation
# if __name__ == "__main__":
#     scraper = DoppelherzScraper()
    
#     # Option 1: Scraper un seul produit
#     product_url = "https://www.doppelherz.ma/fr/produits/doppelherz-aktiv-capilvit"
#     product = scraper.scrape_product(product_url)
    
#     # Sauvegarder un seul produit
#     with open('single_product.json', 'w', encoding='utf-8') as f:
#         json.dump(product, f, ensure_ascii=False, indent=2)
    
#     print("Produit sauvegardé dans single_product.json")
    
#     # Option 2: Scraper plusieurs produits
#     # Liste des URLs de produits à scraper
#     # product_urls = [
#     #     "https://www.doppelherz.ma/fr/produits/doppelherz-aktiv-capilvit",
#     #     # Ajoutez d'autres URLs ici
#     # ]
    
#     # Ou récupérer automatiquement depuis une catégorie
#     # category_url = "https://www.doppelherz.ma/fr/produits/peau-cheveux-et-ongles"
#     # product_urls = scraper.scrape_products_list(category_url)
    
#     # scraper.scrape_all_products(product_urls, 'all_products.json')