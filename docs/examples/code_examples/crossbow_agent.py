import asyncio

from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext


async def main() -> None:
    """Agente que extrae información sobre ballestas desde sitios web.

    Este ejemplo demuestra cómo crear un agente que puede:
    1. Extraer información de productos de ballestas desde tiendas en línea
    2. Extraer especificaciones técnicas, precios y disponibilidad
    3. Almacenar los datos en un formato estructurado para análisis

    Esto es útil para crear comparadores de precios, bases de datos de productos
    o sistemas de monitoreo de inventario.
    """
    # Crear una instancia del crawler optimizada para extraer información de productos
    crawler = BeautifulSoupCrawler(
        # Limitar solicitudes durante las pruebas, eliminar para crawling completo
        max_requests_per_crawl=50,
        # Reintentar solicitudes fallidas
        max_request_retries=3,
        # Configurar tiempo de espera entre solicitudes (en segundos)
        request_handler_timeout=60.0,
    )

    # Definir el manejador de solicitudes para extraer información de ballestas
    @crawler.router.default_handler
    async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
        """Extraer información de productos de ballestas de la página."""
        context.log.info(f'Procesando {context.request.url} ...')

        # Extraer todos los productos de la página
        # Este es un ejemplo genérico - ajustar los selectores según la estructura
        # real del sitio web
        products = context.soup.find_all('div', class_='product-item')

        # Si no se encuentran con esa clase, intentar estructuras alternativas
        if not products:
            products = context.soup.find_all('article', class_='product')
        if not products:
            products = context.soup.find_all('div', {'data-product-id': True})

        for product in products:
            # Extraer nombre del producto
            name_elem = product.find('h2', class_='product-name')
            if not name_elem:
                name_elem = product.find('h3', class_='product-title')
            if not name_elem:
                name_elem = product.find('a', class_='product-link')

            product_name = name_elem.get_text(strip=True) if name_elem else 'Desconocido'

            # Extraer marca
            brand_elem = product.find('span', class_='brand')
            if not brand_elem:
                brand_elem = product.find('div', class_='manufacturer')
            brand = brand_elem.get_text(strip=True) if brand_elem else ''

            # Extraer precio
            price_elem = product.find('span', class_='price')
            if not price_elem:
                price_elem = product.find('div', class_='product-price')
            if not price_elem:
                price_elem = product.find('span', {'data-price': True})

            price = price_elem.get_text(strip=True) if price_elem else 'No disponible'

            # Extraer descuento si existe
            discount_elem = product.find('span', class_='discount')
            if not discount_elem:
                discount_elem = product.find('div', class_='sale-price')
            discount = discount_elem.get_text(strip=True) if discount_elem else ''

            # Extraer especificaciones técnicas
            specs = {}

            # Potencia (draw weight en libras)
            power_elem = product.find('span', class_='draw-weight')
            if not power_elem:
                power_elem = product.find('span', {'data-spec': 'power'})
            if power_elem:
                specs['draw_weight_lbs'] = power_elem.get_text(strip=True)

            # Velocidad (FPS - feet per second)
            speed_elem = product.find('span', class_='fps')
            if not speed_elem:
                speed_elem = product.find('span', {'data-spec': 'speed'})
            if speed_elem:
                specs['speed_fps'] = speed_elem.get_text(strip=True)

            # Peso del producto
            weight_elem = product.find('span', class_='weight')
            if weight_elem:
                specs['weight'] = weight_elem.get_text(strip=True)

            # Longitud
            length_elem = product.find('span', class_='length')
            if length_elem:
                specs['length'] = length_elem.get_text(strip=True)

            # Extraer disponibilidad
            stock_elem = product.find('span', class_='stock-status')
            if not stock_elem:
                stock_elem = product.find('div', class_='availability')
            availability = stock_elem.get_text(strip=True) if stock_elem else 'Desconocido'

            # Extraer calificación si está disponible
            rating_elem = product.find('span', class_='rating')
            if not rating_elem:
                rating_elem = product.find('div', class_='star-rating')
            rating = rating_elem.get_text(strip=True) if rating_elem else ''

            # Extraer número de reseñas
            reviews_elem = product.find('span', class_='review-count')
            reviews_count = reviews_elem.get_text(strip=True) if reviews_elem else '0'

            # Extraer características adicionales
            features = []
            features_list = product.find('ul', class_='product-features')
            if features_list:
                feature_items = features_list.find_all('li')
                features = [item.get_text(strip=True) for item in feature_items]

            # Extraer URL del producto
            link_elem = product.find('a', class_='product-link')
            if not link_elem:
                link_elem = product.find('a', href=True)
            product_url = (
                context.request.urljoin(link_elem['href'])
                if link_elem and link_elem.get('href')
                else context.request.url
            )

            # Extraer imagen del producto
            img_elem = product.find('img', class_='product-image')
            if not img_elem:
                img_elem = product.find('img')
            image_url = img_elem.get('src', '') if img_elem else ''
            if image_url and not image_url.startswith('http'):
                image_url = context.request.urljoin(image_url)

            # Estructurar los datos
            product_data = {
                'url': product_url,
                'source_url': context.request.url,
                'name': product_name,
                'brand': brand,
                'price': price,
                'discount': discount,
                'specifications': specs,
                'availability': availability,
                'rating': rating,
                'reviews_count': reviews_count,
                'features': features,
                'image_url': image_url,
                'extracted_at': context.request.loaded_url,
            }

            # Almacenar los datos extraídos
            await context.push_data(product_data)
            context.log.info(f'Producto extraído: {product_name}')

        # Encontrar y encolar enlaces a más productos
        # Buscar paginación o categorías relacionadas
        await context.enqueue_links(
            selector='a.next-page, a.pagination-link, nav.pagination a, a.category-link',
            label='pagination',
        )

        # También encolar enlaces a páginas de detalles de productos
        await context.enqueue_links(
            selector='a.product-link, a.product-details',
            label='product-details',
        )

    # Manejador específico para páginas de detalles de productos
    @crawler.router.handler('product-details')
    async def product_details_handler(context: BeautifulSoupCrawlingContext) -> None:
        """Extraer información detallada de la página de detalles del producto."""
        context.log.info(f'Procesando detalles de producto: {context.request.url}')

        # Extraer información más detallada de la página de producto individual
        title_elem = context.soup.find('h1', class_='product-title')
        title = title_elem.get_text(strip=True) if title_elem else ''

        # Extraer descripción completa
        desc_elem = context.soup.find('div', class_='product-description')
        description = desc_elem.get_text(strip=True) if desc_elem else ''

        # Extraer tabla de especificaciones completas
        specs_table = context.soup.find('table', class_='specifications')
        detailed_specs = {}
        if specs_table:
            rows = specs_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    detailed_specs[key] = value

        # Extraer todas las imágenes del producto
        images = []
        img_gallery = context.soup.find('div', class_='product-gallery')
        if img_gallery:
            img_elements = img_gallery.find_all('img')
            for img in img_elements:
                img_url = img.get('src', '')
                if img_url and not img_url.startswith('http'):
                    img_url = context.request.urljoin(img_url)
                if img_url:
                    images.append(img_url)

        detailed_data = {
            'url': context.request.url,
            'title': title,
            'description': description,
            'detailed_specifications': detailed_specs,
            'images': images,
        }

        await context.push_data(detailed_data)

    # Ejecutar el crawler con las URLs iniciales
    # Reemplazar estas con tiendas reales de ballestas y equipamiento
    await crawler.run(
        [
            'https://example.com/crossbows',
            'https://example.com/archery-equipment',
            # Agregar más URLs según sea necesario
        ]
    )


if __name__ == '__main__':
    asyncio.run(main())
