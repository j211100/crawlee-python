import asyncio

from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext


async def main() -> None:
    """Agente que extrae y responde preguntas de la prueba de conducir.

    Este ejemplo demuestra cómo crear un agente que puede:
    1. Extraer preguntas de la prueba de conducir desde sitios web
    2. Extraer el texto de la pregunta, opciones y respuestas correctas
    3. Almacenar los datos en un formato estructurado para referencia futura

    Esto es útil para crear materiales de estudio o pruebas de práctica.
    """
    # Crear una instancia del crawler optimizada para extraer contenido
    # de pruebas de conducir
    crawler = BeautifulSoupCrawler(
        # Limitar solicitudes durante las pruebas, eliminar para crawling completo
        max_requests_per_crawl=50,
        # Reintentar solicitudes fallidas
        max_request_retries=2,
    )

    # Definir el manejador de solicitudes para extraer preguntas de la prueba de conducir
    @crawler.router.default_handler
    async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
        """Extraer preguntas y respuestas de la prueba de conducir de la página."""
        context.log.info(f'Procesando {context.request.url} ...')

        # Extraer todas las preguntas de la página
        # Este es un ejemplo genérico - ajustar los selectores según la estructura
        # real del sitio web
        questions = context.soup.find_all('div', class_='question')

        for idx, question_element in enumerate(questions, 1):
            # Extraer texto de la pregunta
            question_text_elem = question_element.find('p', class_='question-text')
            if not question_text_elem:
                question_text_elem = question_element.find('h3')

            if question_text_elem:
                question_text = question_text_elem.get_text(strip=True)
            else:
                continue

            # Extraer opciones (típicamente A, B, C, D)
            options = []
            option_elements = question_element.find_all('li', class_='option')
            if not option_elements:
                # Intentar estructura alternativa
                option_elements = question_element.find_all('div', class_='answer-option')

            for option in option_elements:
                option_text = option.get_text(strip=True)
                options.append(option_text)

            # Extraer la respuesta correcta
            correct_answer_elem = question_element.find('span', class_='correct-answer')
            if not correct_answer_elem:
                correct_answer_elem = question_element.find('div', class_='answer')

            if correct_answer_elem:
                correct_answer = correct_answer_elem.get_text(strip=True)
            else:
                correct_answer = 'No especificada'

            # Extraer explicación si está disponible
            explanation_elem = question_element.find('div', class_='explanation')
            explanation = (
                explanation_elem.get_text(strip=True) if explanation_elem else ''
            )

            # Estructurar los datos
            question_data = {
                'question_number': idx,
                'url': context.request.url,
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation,
            }

            # Almacenar los datos extraídos
            await context.push_data(question_data)
            context.log.info(f'Pregunta extraída {idx}: {question_text[:50]}...')

        # Encontrar y encolar enlaces a más preguntas
        # Buscar paginación o páginas de preguntas relacionadas
        await context.enqueue_links(
            selector='a.next-page, a.more-questions, nav.pagination a',
        )

    # Ejecutar el crawler con las URLs iniciales
    # Reemplazar estas con sitios web reales de preguntas de prueba de conducir
    # Los ejemplos podrían incluir pruebas de práctica oficiales del DMV
    # o sitios educativos
    await crawler.run(
        [
            'https://example.com/driving-test-questions',
            # Agregar más URLs según sea necesario
        ]
    )


if __name__ == '__main__':
    asyncio.run(main())
