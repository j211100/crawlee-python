import asyncio

from playwright.async_api import Page

from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext


async def main() -> None:
    """Agente interactivo para preguntas de la prueba de conducir usando Playwright.

    Este ejemplo demuestra cómo crear un agente que puede:
    1. Navegar sitios web de pruebas de conducir con JavaScript intensivo
    2. Interactuar con cuestionarios y pruebas interactivas
    3. Extraer preguntas, seleccionar respuestas y verificar resultados
    4. Almacenar datos completos de la prueba

    Usar esto cuando se trabaje con sitios web dinámicos que requieren
    interacción con el navegador.
    """
    # Crear un crawler de Playwright para sitios con JavaScript intensivo
    crawler = PlaywrightCrawler(
        # Limitar solicitudes durante las pruebas
        max_requests_per_crawl=20,
        # Establecer en False para ver el navegador en acción (útil para depuración)
        headless=True,
        # Reintentar solicitudes fallidas
        max_request_retries=2,
    )

    # Definir el manejador de solicitudes para páginas de prueba interactivas
    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        """Manejar páginas interactivas de prueba de conducir."""
        context.log.info(f'Procesando {context.request.url} ...')

        # Esperar a que la página se cargue completamente
        await context.page.wait_for_load_state('networkidle')

        # Ejemplo: Extraer preguntas de un cuestionario interactivo
        # Ajustar los selectores según la estructura real del sitio web

        # Encontrar todos los contenedores de preguntas
        questions = await context.page.query_selector_all(
            '.quiz-question, .test-question'
        )

        for idx, question_element in enumerate(questions, 1):
            # Extraer texto de la pregunta
            question_text = await question_element.query_selector('.question-text, h3')
            if question_text:
                question_text = await question_text.inner_text()
            else:
                continue

            # Extraer opciones de respuesta
            options = []
            option_elements = await question_element.query_selector_all(
                '.answer-option, .option, input[type="radio"] + label'
            )

            for option_elem in option_elements:
                option_text = await option_elem.inner_text()
                options.append(option_text.strip())

            # Intentar encontrar la respuesta correcta (si está revelada)
            correct_answer = ''
            correct_elem = await question_element.query_selector('.correct, .answer-key')
            if correct_elem:
                correct_answer = await correct_elem.inner_text()

            # Verificar si hay una explicación
            explanation = ''
            explanation_elem = await question_element.query_selector(
                '.explanation, .answer-explanation'
            )
            if explanation_elem:
                explanation = await explanation_elem.inner_text()

            # Extraer cualquier imagen (como señales de tráfico)
            images = []
            image_elements = await question_element.query_selector_all('img')
            for img in image_elements:
                img_src = await img.get_attribute('src')
                img_alt = await img.get_attribute('alt')
                if img_src:
                    images.append({'src': img_src, 'alt': img_alt or ''})

            # Estructurar los datos
            question_data = {
                'question_number': idx,
                'url': context.request.url,
                'question': question_text.strip(),
                'options': options,
                'correct_answer': correct_answer.strip(),
                'explanation': explanation.strip(),
                'images': images,
                'category': await extract_category(context.page),
            }

            # Almacenar los datos extraídos
            await context.push_data(question_data)
            context.log.info(f'Pregunta extraída {idx}: {question_text[:50]}...')

        # Buscar botones "Siguiente" o "Continuar" para navegar a más preguntas
        try:
            next_button = await context.page.query_selector(
                'button.next, a.next-page, button:has-text("Next"), '
                'button:has-text("Continue")'
            )
            if next_button:
                next_url = await next_button.get_attribute('href')
                if next_url:
                    await context.enqueue_links(selector='button.next, a.next-page')
        except (TimeoutError, AttributeError):
            # Esperado: No todas las páginas tienen botones de siguiente
            pass

        # Encolar enlaces a otras categorías de prueba o conjuntos de preguntas
        await context.enqueue_links(
            selector='a[href*="test"], a[href*="quiz"], a[href*="questions"]',
        )

    # Ejecutar el crawler con las URLs iniciales
    # Reemplazar con sitios web reales de prueba de conducir
    await crawler.run(
        [
            'https://example.com/driving-test',
            # Agregar más URLs según sea necesario
        ]
    )


async def extract_category(page: Page) -> str:
    """Extraer la categoría/tema de las preguntas de la prueba de conducir."""
    try:
        # Intentar encontrar información de categoría
        category_elem = await page.query_selector('.category, .topic, .test-category')
        if category_elem:
            return await category_elem.inner_text()

        # Intentar extraer del título de la página
        title = await page.title()
        if 'category' in title.lower() or 'topic' in title.lower():
            return title

    except (TimeoutError, AttributeError):
        # Devolver categoría predeterminada si falla la extracción
        return 'General'

    return 'General'


if __name__ == '__main__':
    asyncio.run(main())
