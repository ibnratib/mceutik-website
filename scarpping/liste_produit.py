import requests
from bs4 import BeautifulSoup
import json
import re
import time

from urllib.parse import urlparse

def extract_product_slug(url: str) -> str:
    """
    Extrait le slug du produit à partir d'une URL.
    Exemple :
    "https://www.doppelherz.ma/fr/produits/doppelherz-aktiv-aktiv-detox"
    → "doppelherz-aktiv-aktiv-detox"
    """
    try:
        parsed = urlparse(url)
        path = parsed.path
        
        # Supprime le trailing slash s'il existe
        if path.endswith('/'):
            path = path[:-1]
        
        # Retourne la dernière partie après le dernier "/"
        if '/' in path:
            return path.split('/')[-1]
        else:
            return path  # au cas où le path serait juste le slug
    except Exception as e:
        print(f"URL invalide : {e}")
        return ""

def scraper_produits_doppelherz():

    # URL of the products page
    url = "https://www.doppelherz.ma/fr/produits"

    # Fetch the page content
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # List to hold all products
    products = []

    # Find all product articles
    for article in soup.find_all('article', class_='blow-up-link'):
        # Extract image URL (using the largest srcset from the first source)
        picture = article.find('picture')
        image_url = ''
        if picture:
            source = picture.find('source')
            if source and 'srcset' in source.attrs:
                image_url = source['srcset']  # This is the 406x406 webp image

        # Extract brand (e.g., "Doppelherz aktiv")
        brand_elem = article.find('p', class_='mt-auto')
        brand = brand_elem.text.strip() if brand_elem else ''

        # Extract title (e.g., "A-Z Depot")
        title_elem = article.find('h3')
        title = title_elem.text.strip() if title_elem else ''

        # Extract link (full URL)
        link_elem = article.find('a', href=True)
        link = ''
        if link_elem and 'href' in link_elem.attrs:
            link = "https://www.doppelherz.ma" + link_elem['href']

        # Extract type (e.g., "Complément alimentaire")
        type_elem = article.find('div', class_='mb-0.5')
        product_type = ''
        if type_elem:
            # Remove the sr-only span text
            sr_only = type_elem.find('span', class_='sr-only')
            if sr_only:
                sr_only.extract()
            product_type = type_elem.text.strip()

        # Extract size (e.g., "30 comprimés")
        size_elem = article.find('div', class_=lambda x: x and 'theme-stozzon:!mt-4' in x)
        size = ''
        if size_elem:
            # Remove the sr-only span text
            sr_only = size_elem.find('span', class_='sr-only')
            if sr_only:
                sr_only.extract()
            size = size_elem.text.strip()

        # Optional: Extract sticker if present (e.g., "Nouveau !")
        sticker_elem = article.find('div', class_='sticker')
        sticker = sticker_elem.text.strip() if sticker_elem else ''

        # Append to products list
        products.append({
            'brand': brand,
            'title': title,
            'type': product_type,
            'size': size,
            'image_url': image_url,
            'detail_link': link,
            'sticker': sticker,
            'slug': extract_product_slug(link)
        })

    # Save to JSON file
    with open('produits_doppelherz.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print("Products scraped and saved to 'produits_doppelherz.json'")


def clean_html(element):
    """
    Recursively remove unwanted attributes (class, style, id, data-*, etc.)
    Keep only essential attributes like src, alt, href.
    Skip non-element nodes safely.
    """
    if not element or not hasattr(element, 'name'):
        return element  # Skip strings, comments, etc.

    # Remove unwanted attributes
    unwanted_attrs = ['class', 'style', 'id', 'data-v-', 'aria-hidden', 'aria-label', 
                      'role', 'tabindex', 'loading', 'width', 'height']
    for attr in list(element.attrs.keys()):
        if any(attr.startswith(prefix) for prefix in unwanted_attrs):
            del element.attrs[attr]
        # Keep only src, alt, href
        elif attr not in ['src', 'alt', 'href']:
            del element.attrs[attr]

    # Recurse into children safely
    for child in element.contents:  # Use .contents instead of .children to include all
        if isinstance(child, Comment):
            child.extract()  # Optional: remove HTML comments entirely
        elif hasattr(child, 'name'):  # Only recurse into tag elements
            clean_html(child)

    return element

def clean_content_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # 1️⃣ Supprimer tous les commentaires
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 2️⃣ Supprimer tous les attributs inutiles et gérer les images
    for tag in soup.find_all(True):
        if tag.name == "img":
            tag.decompose()  # supprime complètement la balise <img>
        else:
            tag.attrs = {}  # garde le tag mais supprime tous les attributs

    # 3️⃣ Nettoyer les div imbriqués dans les titres
    for header in soup.find_all(['h1','h2','h3','h4','h5','h6']):
        for div in header.find_all('div'):
            div.unwrap()  # supprime le div mais garde le texte

    # 4️⃣ Transformer les div seuls en <p>
    for div in soup.find_all('div'):
        div.name = 'p'

    return str(soup)
from bs4 import Comment
def scrape_product(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch page: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')

    data = {}

    data['slug'] = extract_product_slug(url)
    # 1. Brand (e.g., "Doppelherz aktiv")
    brand_tag = soup.select_one('h1 div a')
    data['brand'] = brand_tag.get_text(strip=True) if brand_tag else ""

    # 2. Product title (e.g., "A-Z Depot")
    title_tag = soup.select_one('h1 span')
    data['title'] = title_tag.get_text(strip=True) if title_tag else ""

    # 3. Category (e.g., "Complément alimentaire")
    category_tag = soup.select_one('div.flex.flex-col.md\\:flex-row > div')
    data['category'] = category_tag.get_text(strip=True) if category_tag else ""

    # 3. Subtitle (e.g., "Cure de vitamines et minéraux")
    subtitle_tag = soup.select_one('hgroup p')
    data['subtitle'] = subtitle_tag.get_text(strip=True) if subtitle_tag else ""

    # 4. Features list (bullet points on the right)
    features = []
    features_ul = soup.select_one('.arrow-list ul')
    if features_ul:
        for li in features_ul.find_all('li', recursive=False):
            text = li.get_text(strip=True)
            if text:
                features.append(text)
    data['features'] = features

    # 5. Images (main product images + icons if needed)
    img_tags = soup.find_all('img')
    images = []
    seen = set()
    for img in img_tags:
        src = img.get('src')
        if src and src not in seen:
            # Optional: filter only product-relevant images (exclude tiny icons if needed)
            if 'image-thumb' in src or 'pim.doppelherz' in src:
                images.append(src)
                seen.add(src)
    data['images'] = images

    # 6. Product information section (full HTML cleaned)
    info_section = soup.find('div', id='tab-content-information')
    if info_section:
        # Work on a copy to avoid modifying original soup
        cleaned = clean_html(info_section.__copy__())
        # Convert to string and remove outer div wrapper
        html_str = str(cleaned)
        if html_str.startswith('<div') and html_str.endswith('</div>'):
            # Remove outer <div>...</div>
            html_str = html_str[html_str.find('>') + 1 : html_str.rfind('</div>')].strip()
        data['information_html'] = html_str
    else:
        data['information_html'] = ""
    data['information_html'] = clean_content_html(data['information_html'])
    return data

