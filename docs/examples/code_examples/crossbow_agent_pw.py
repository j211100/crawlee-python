import asyncio

from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext


async def main() -> None:
    """Agente que extrae información sobre ballestas usando Playwright.

    Este ejemplo demuestra cómo crear un agente que puede:
    1. Extraer información de productos de ballestas desde tiendas con JavaScript
    2. Interactuar con filtros y catálogos dinámicos
    3. Capturar imágenes de productos en alta resolución
    4. Manejar carga dinámica y paginación infinita

    Usar PlaywrightCrawler cuando el sitio web requiere JavaScript para mostrar
    el contenido o tiene elementos interactivos.
    """
    # Crear una instancia del crawler con Playwright
    crawler = PlaywrightCrawler(
        # Limitar solicitudes durante las pruebas
        max_requests_per_crawl=30,
        # Reintentar solicitudes fallidas
        max_request_retries=3,
        # Configurar tiempo de espera
        request_handler_timeout=120.0,
        # Configurar el navegador
        headless=True,  # Cambiar a False para ver el navegador en acción
    )

    # Definir el manejador de solicitudes principal
    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        """Extraer información de productos de ballestas usando Playwright."""
        context.log.info(f'Procesando {context.request.url} ...')

        # Esperar a que el contenido dinámico se cargue
        try:
            await context.page.wait_for_selector(
                '.product-item, .product-card, [data-product-id]',
                timeout=10000,
            )
        except Exception as e:
            context.log.warning(f'Tiempo de espera agotado esperando productos: {e}')
            return

        # Scroll para activar carga dinámica (lazy loading)
        await context.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await context.page.wait_for_timeout(2000)  # Esperar carga de imágenes

        # Extraer productos usando JavaScript
        products_data = await context.page.evaluate("""
            () => {
                const products = [];
                const productElements = document.querySelectorAll(
                    '.product-item, .product-card, article.product, [data-product-id]'
                );

                productElements.forEach(product => {
                    // Extraer nombre
                    const nameElem = product.querySelector(
                        'h2.product-name, h3.product-title, .product-name, a.product-link'
                    );
                    const name = nameElem ? nameElem.textContent.trim() : 'Desconocido';

                    // Extraer marca
                    const brandElem = product.querySelector('.brand, .manufacturer');
                    const brand = brandElem ? brandElem.textContent.trim() : '';

                    // Extraer precio
                    const priceElem = product.querySelector(
                        '.price, .product-price, [data-price]'
                    );
                    const price = priceElem ? priceElem.textContent.trim() : 'No disponible';

                    // Extraer descuento
                    const discountElem = product.querySelector('.discount, .sale-price');
                    const discount = discountElem ? discountElem.textContent.trim() : '';

                    // Extraer especificaciones
                    const specs = {};
                    const drawWeightElem = product.querySelector(
                        '.draw-weight, [data-spec="power"]'
                    );
                    if (drawWeightElem) {
                        specs.draw_weight_lbs = drawWeightElem.textContent.trim();
                    }

                    const speedElem = product.querySelector('.fps, [data-spec="speed"]');
                    if (speedElem) {
                        specs.speed_fps = speedElem.textContent.trim();
                    }

                    const weightElem = product.querySelector('.weight, [data-spec="weight"]');
                    if (weightElem) {
                        specs.weight = weightElem.textContent.trim();
                    }

                    const lengthElem = product.querySelector('.length, [data-spec="length"]');
                    if (lengthElem) {
                        specs.length = lengthElem.textContent.trim();
                    }

                    // Extraer disponibilidad
                    const stockElem = product.querySelector('.stock-status, .availability');
                    const availability = stockElem ? stockElem.textContent.trim() : 'Desconocido';

                    // Extraer calificación
                    const ratingElem = product.querySelector('.rating, .star-rating');
                    const rating = ratingElem ? ratingElem.textContent.trim() : '';

                    // Extraer número de reseñas
                    const reviewsElem = product.querySelector('.review-count');
                    const reviews_count = reviewsElem ? reviewsElem.textContent.trim() : '0';

                    // Extraer características
                    const features = [];
                    const featuresList = product.querySelector('ul.product-features');
                    if (featuresList) {
                        const items = featuresList.querySelectorAll('li');
                        items.forEach(item => {
                            features.push(item.textContent.trim());
                        });
                    }

                    // Extraer URL del producto
                    const linkElem = product.querySelector('a.product-link, a[href]');
                    const productUrl = linkElem ? linkElem.href : '';

                    // Extraer imagen
                    const imgElem = product.querySelector('img.product-image, img');
                    const imageUrl = imgElem ? imgElem.src : '';

                    products.push({
                        name,
                        brand,
                        price,
                        discount,
                        specifications: specs,
                        availability,
                        rating,
                        reviews_count,
                        features,
                        product_url: productUrl,
                        image_url: imageUrl,
                    });
                });

                return products;
            }
        """)

        # Procesar y almacenar cada producto
        for product in products_data:
            product_data = {
                'url': product.get('product_url', ''),
                'source_url': context.request.url,
                'name': product.get('name', ''),
                'brand': product.get('brand', ''),
                'price': product.get('price', ''),
                'discount': product.get('discount', ''),
                'specifications': product.get('specifications', {}),
                'availability': product.get('availability', ''),
                'rating': product.get('rating', ''),
                'reviews_count': product.get('reviews_count', '0'),
                'features': product.get('features', []),
                'image_url': product.get('image_url', ''),
            }

            await context.push_data(product_data)
            context.log.info(f'Producto extraído: {product_data["name"]}')

        # Manejar paginación
        # Buscar botón "siguiente" o enlaces de paginación
        try:
            next_button = await context.page.query_selector(
                'a.next-page, button.next, a.pagination-next, [aria-label="Next"]'
            )
            if next_button:
                next_url = await next_button.get_attribute('href')
                if next_url:
                    await context.enqueue_links(
                        selector='a.next-page, a.pagination-next',
                        label='pagination',
                    )
        except Exception as e:
            context.log.warning(f'Error al buscar paginación: {e}')

        # Encolar enlaces a detalles de productos
        await context.enqueue_links(
            selector='a.product-link, a.product-details',
            label='product-details',
        )

        # Encolar enlaces a categorías relacionadas
        await context.enqueue_links(
            selector='a.category-link',
            label='category',
        )

    # Manejador para páginas de detalles de productos
    @crawler.router.handler('product-details')
    async def product_details_handler(context: PlaywrightCrawlingContext) -> None:
        """Extraer información detallada de la página de producto."""
        context.log.info(f'Procesando detalles: {context.request.url}')

        # Esperar a que se cargue el contenido principal
        try:
            await context.page.wait_for_selector(
                'h1.product-title, .product-description',
                timeout=10000,
            )
        except Exception:
            context.log.warning('No se pudo cargar la página de detalles')
            return

        # Extraer título
        title = await context.page.text_content('h1.product-title, h1')
        title = title.strip() if title else ''

        # Extraer descripción completa
        description = ''
        desc_elem = await context.page.query_selector(
            '.product-description, .description, #description'
        )
        if desc_elem:
            description = await desc_elem.text_content()
            description = description.strip() if description else ''

        # Extraer especificaciones detalladas
        detailed_specs = {}
        spec_rows = await context.page.query_selector_all(
            'table.specifications tr, .specs-table tr'
        )
        for row in spec_rows:
            cells = await row.query_selector_all('td, th')
            if len(cells) >= 2:
                key = await cells[0].text_content()
                value = await cells[1].text_content()
                if key and value:
                    detailed_specs[key.strip()] = value.strip()

        # Capturar todas las imágenes del producto
        images = []
        img_elements = await context.page.query_selector_all(
            '.product-gallery img, .product-images img, [data-image]'
        )
        for img in img_elements[:10]:  # Limitar a 10 imágenes
            img_url = await img.get_attribute('src')
            if img_url and not img_url.startswith('data:'):
                images.append(img_url)

        # Capturar pantalla del producto (opcional)
        # screenshot_bytes = await context.page.screenshot(full_page=False)
        # Guardar screenshot si es necesario

        # Extraer reseñas de usuarios
        reviews = []
        review_elements = await context.page.query_selector_all(
            '.review-item, .user-review, [data-review]'
        )
        for review_elem in review_elements[:5]:  # Limitar a 5 reseñas
            try:
                author_elem = await review_elem.query_selector('.review-author, .author')
                author = (
                    await author_elem.text_content() if author_elem else 'Anónimo'
                )

                rating_elem = await review_elem.query_selector('.review-rating, .rating')
                rating = (
                    await rating_elem.text_content() if rating_elem else ''
                )

                comment_elem = await review_elem.query_selector(
                    '.review-text, .comment'
                )
                comment = (
                    await comment_elem.text_content() if comment_elem else ''
                )

                reviews.append({
                    'author': author.strip() if author else '',
                    'rating': rating.strip() if rating else '',
                    'comment': comment.strip() if comment else '',
                })
            except Exception as e:
                context.log.warning(f'Error al extraer reseña: {e}')
                continue

        detailed_data = {
            'url': context.request.url,
            'title': title,
            'description': description,
            'detailed_specifications': detailed_specs,
            'images': images,
            'reviews': reviews,
        }

        await context.push_data(detailed_data)

    # Manejador para páginas de categoría
    @crawler.router.handler('category')
    async def category_handler(context: PlaywrightCrawlingContext) -> None:
        """Manejar páginas de categoría y aplicar filtros."""
        context.log.info(f'Procesando categoría: {context.request.url}')

        # Esperar a que se carguen los filtros
        await context.page.wait_for_timeout(2000)

        # Ejemplo: Aplicar filtros (ajustar según el sitio)
        try:
            # Expandir filtros si están colapsados
            filter_buttons = await context.page.query_selector_all(
                'button.filter-toggle, .expand-filters'
            )
            for button in filter_buttons:
                await button.click()
                await context.page.wait_for_timeout(500)

            # Seleccionar rango de precio (ejemplo)
            # price_filter = await context.page.query_selector('#price-range')
            # if price_filter:
            #     await price_filter.fill('100-500')

        except Exception as e:
            context.log.warning(f'Error al aplicar filtros: {e}')

        # Procesar productos en la categoría (llamar al handler por defecto)
        await request_handler(context)

    # Ejecutar el crawler con las URLs iniciales
    await crawler.run(
        [
            'https://example.com/crossbows',
            'https://example.com/hunting-equipment',
            # Agregar más URLs según sea necesario
        ]
    )


if __name__ == '__main__':
    asyncio.run(main())
