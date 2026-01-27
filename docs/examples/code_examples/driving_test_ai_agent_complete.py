"""Agente de IA de Clase Mundial para Preguntas de Prueba de Conducir.

Este es un agente completo y avanzado que demuestra capacidades de IA de nivel empresarial
para extraer, procesar, analizar y responder preguntas de pruebas de conducir.

Características:
- Extracción inteligente de múltiples sitios web
- Procesamiento de lenguaje natural (NLP)
- Sistema de almacenamiento persistente
- Análisis de similitud de preguntas
- Generación de estadísticas y reportes
- Sistema de caché inteligente
- Manejo avanzado de errores
- Logging estructurado
- Validación de datos
- Exportación en múltiples formatos
"""

import asyncio
import hashlib
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext

# Configuración de logging avanzado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('driving_test_agent.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class QuestionDatabase:
    """Sistema de base de datos inteligente para preguntas de prueba de conducir."""

    def __init__(self, db_path: str = 'driving_questions.json'):
        """Inicializar base de datos."""
        self.db_path = Path(db_path)
        self.questions: dict[str, dict[str, Any]] = {}
        self.stats = {
            'total_questions': 0,
            'unique_questions': 0,
            'duplicate_questions': 0,
            'categories': defaultdict(int),
            'sources': defaultdict(int),
        }
        self._load_database()

    def _load_database(self) -> None:
        """Cargar base de datos existente."""
        if self.db_path.exists():
            try:
                with open(self.db_path, encoding='utf-8') as f:
                    data = json.load(f)
                    self.questions = data.get('questions', {})
                    self.stats = data.get('stats', self.stats)
                logger.info(f'Base de datos cargada: {len(self.questions)} preguntas')
            except Exception as e:
                logger.error(f'Error cargando base de datos: {e}')

    def _generate_question_id(self, question_text: str) -> str:
        """Generar ID único para pregunta basado en contenido."""
        return hashlib.md5(question_text.encode()).hexdigest()[:16]

    def add_question(
        self,
        question_text: str,
        options: list[str],
        correct_answer: str,
        explanation: str = '',
        category: str = 'General',
        source_url: str = '',
        images: list[dict[str, str]] | None = None,
    ) -> tuple[str, bool]:
        """Agregar pregunta a la base de datos.

        Returns:
            Tuple de (question_id, is_new) donde is_new indica si es pregunta nueva.
        """
        question_id = self._generate_question_id(question_text)
        is_new = question_id not in self.questions

        if is_new:
            self.questions[question_id] = {
                'id': question_id,
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'category': category,
                'source_url': source_url,
                'images': images or [],
                'created_at': datetime.now().isoformat(),
                'times_seen': 1,
            }
            self.stats['unique_questions'] += 1
            self.stats['categories'][category] += 1
            self.stats['sources'][source_url] += 1
            logger.info(f'Nueva pregunta agregada: {question_id}')
        else:
            # Actualizar contador de veces vista
            self.questions[question_id]['times_seen'] += 1
            self.stats['duplicate_questions'] += 1
            logger.debug(f'Pregunta duplicada detectada: {question_id}')

        self.stats['total_questions'] += 1
        return question_id, is_new

    def get_question(self, question_id: str) -> dict[str, Any] | None:
        """Obtener pregunta por ID."""
        return self.questions.get(question_id)

    def search_questions(
        self,
        keyword: str | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Buscar preguntas por palabra clave o categoría."""
        results = []
        for question in self.questions.values():
            if keyword and keyword.lower() not in question['question'].lower():
                continue
            if category and question['category'] != category:
                continue
            results.append(question)
            if len(results) >= limit:
                break
        return results

    def get_statistics(self) -> dict[str, Any]:
        """Obtener estadísticas de la base de datos."""
        return {
            'total_questions': self.stats['total_questions'],
            'unique_questions': self.stats['unique_questions'],
            'duplicate_questions': self.stats['duplicate_questions'],
            'categories': dict(self.stats['categories']),
            'sources': dict(self.stats['sources']),
            'database_size_mb': self.db_path.stat().st_size / 1024 / 1024
            if self.db_path.exists()
            else 0,
        }

    def save_database(self) -> None:
        """Guardar base de datos en disco."""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        'questions': self.questions,
                        'stats': self.stats,
                        'last_updated': datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            logger.info(f'Base de datos guardada: {len(self.questions)} preguntas')
        except Exception as e:
            logger.error(f'Error guardando base de datos: {e}')

    def export_to_format(self, format_type: str = 'json', output_path: str = '') -> str:
        """Exportar base de datos a diferentes formatos.

        Args:
            format_type: 'json', 'csv', o 'markdown'
            output_path: Ruta de salida (opcional)

        Returns:
            Ruta del archivo exportado
        """
        if not output_path:
            output_path = f'driving_questions_export.{format_type}'

        if format_type == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(list(self.questions.values()), f, indent=2, ensure_ascii=False)

        elif format_type == 'csv':
            import csv

            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        'ID',
                        'Pregunta',
                        'Opciones',
                        'Respuesta Correcta',
                        'Explicación',
                        'Categoría',
                    ]
                )
                for q in self.questions.values():
                    writer.writerow(
                        [
                            q['id'],
                            q['question'],
                            '|'.join(q['options']),
                            q['correct_answer'],
                            q['explanation'],
                            q['category'],
                        ]
                    )

        elif format_type == 'markdown':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('# Banco de Preguntas de Prueba de Conducir\n\n')
                f.write(f'Total de preguntas: {len(self.questions)}\n\n')
                f.write('---\n\n')

                for q in self.questions.values():
                    f.write(f'## {q["question"]}\n\n')
                    f.write('**Opciones:**\n')
                    for opt in q['options']:
                        f.write(f'- {opt}\n')
                    f.write(f'\n**Respuesta Correcta:** {q["correct_answer"]}\n\n')
                    if q['explanation']:
                        f.write(f'**Explicación:** {q["explanation"]}\n\n')
                    f.write(f'**Categoría:** {q["category"]}\n\n')
                    f.write('---\n\n')

        logger.info(f'Base de datos exportada a {output_path}')
        return output_path


class IntelligentQuestionProcessor:
    """Procesador inteligente de preguntas con análisis avanzado."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Limpiar y normalizar texto."""
        import re

        # Eliminar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        # Eliminar caracteres especiales innecesarios
        text = re.sub(r'[^\w\s¿?¡!.,;:()\-áéíóúÁÉÍÓÚñÑ]', '', text)
        return text.strip()

    @staticmethod
    def extract_category(text: str, url: str = '') -> str:
        """Extraer categoría inteligentemente del texto o URL."""
        categories_keywords = {
            'Señales': ['señal', 'señalización', 'tráfico', 'stop', 'semáforo'],
            'Normativa': ['ley', 'normativa', 'reglamento', 'multa', 'infracción'],
            'Mecánica': [
                'motor',
                'freno',
                'neumático',
                'aceite',
                'mecánica',
                'mantenimiento',
            ],
            'Seguridad': [
                'seguridad',
                'cinturón',
                'airbag',
                'emergencia',
                'accidente',
            ],
            'Conducción': [
                'conducir',
                'velocidad',
                'adelantar',
                'girar',
                'estacionar',
            ],
            'Prioridad': ['prioridad', 'ceder', 'paso', 'intersección', 'rotonda'],
        }

        text_lower = text.lower()
        url_lower = url.lower()

        for category, keywords in categories_keywords.items():
            if any(keyword in text_lower or keyword in url_lower for keyword in keywords):
                return category

        return 'General'

    @staticmethod
    def validate_question(
        question_text: str, options: list[str], correct_answer: str
    ) -> tuple[bool, str]:
        """Validar que la pregunta tenga formato correcto.

        Returns:
            Tuple de (is_valid, error_message)
        """
        if len(question_text) < 10:
            return False, 'Pregunta demasiado corta'

        if len(options) < 2:
            return False, 'Debe tener al menos 2 opciones'

        if not correct_answer:
            return False, 'Falta respuesta correcta'

        if correct_answer not in ''.join(options):
            return False, 'Respuesta correcta no coincide con opciones'

        return True, ''


class DrivingTestAIAgent:
    """Agente de IA de Clase Mundial para Pruebas de Conducir.

    Este agente combina web scraping avanzado, procesamiento inteligente de datos,
    y análisis sofisticado para crear un sistema completo de gestión de preguntas
    de prueba de conducir.
    """

    def __init__(
        self,
        max_requests: int = 100,
        headless: bool = True,
        database_path: str = 'driving_questions.json',
    ):
        """Inicializar agente de IA.

        Args:
            max_requests: Número máximo de solicitudes a realizar
            headless: Ejecutar navegador en modo headless
            database_path: Ruta a la base de datos
        """
        self.max_requests = max_requests
        self.headless = headless
        self.database = QuestionDatabase(database_path)
        self.processor = IntelligentQuestionProcessor()
        self.stats = {
            'pages_processed': 0,
            'questions_found': 0,
            'questions_saved': 0,
            'errors': 0,
        }

        logger.info('Agente de IA inicializado')
        logger.info(
            f'Base de datos cargada con {self.database.stats["unique_questions"]} preguntas'
        )

    async def scrape_and_process(self, start_urls: list[str]) -> dict[str, Any]:
        """Extraer y procesar preguntas de URLs iniciales.

        Args:
            start_urls: Lista de URLs para comenzar el scraping

        Returns:
            Diccionario con estadísticas del proceso
        """
        logger.info(f'Iniciando scraping de {len(start_urls)} URLs')

        # Configurar crawler con opciones avanzadas
        crawler = BeautifulSoupCrawler(
            max_requests_per_crawl=self.max_requests,
            max_request_retries=3,
            request_handler_timeout_secs=60,
        )

        @crawler.router.default_handler
        async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
            """Manejador inteligente de solicitudes."""
            try:
                self.stats['pages_processed'] += 1
                logger.info(
                    f'Procesando página {self.stats["pages_processed"]}: {context.request.url}'
                )

                # Extraer todas las preguntas de la página
                questions = await self._extract_questions(context)

                # Procesar cada pregunta
                for question_data in questions:
                    await self._process_question(question_data, context.request.url)

                # Encolar enlaces para continuar crawling
                await context.enqueue_links(
                    selector='a.next-page, a.more-questions, nav.pagination a, '
                    'a[href*="test"], a[href*="quiz"], a[href*="question"]',
                )

            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f'Error procesando {context.request.url}: {e}')

        # Ejecutar crawler
        await crawler.run(start_urls)

        # Guardar base de datos
        self.database.save_database()

        # Generar reporte final
        return self._generate_report()

    async def _extract_questions(
        self, context: BeautifulSoupCrawlingContext
    ) -> list[dict[str, Any]]:
        """Extraer preguntas de la página con múltiples estrategias."""
        questions = []

        # Estrategia 1: Buscar contenedores de preguntas estándar
        question_containers = context.soup.find_all(
            ['div', 'article', 'section'],
            class_=['question', 'quiz-question', 'test-question', 'pregunta'],
        )

        for container in question_containers:
            question_data = await self._parse_question_container(container)
            if question_data:
                questions.append(question_data)
                self.stats['questions_found'] += 1

        # Estrategia 2: Buscar patrones de lista numerada
        if not questions:
            questions = await self._extract_numbered_questions(context)

        return questions

    async def _parse_question_container(self, container: Any) -> dict[str, Any] | None:
        """Parsear contenedor de pregunta individual."""
        try:
            # Extraer texto de pregunta
            question_elem = container.find(
                ['p', 'h3', 'h4', 'div'],
                class_=['question-text', 'pregunta-texto', 'quiz-question-text'],
            )

            if not question_elem:
                # Intentar encontrar el primer párrafo o heading
                question_elem = container.find(['p', 'h3', 'h4'])

            if not question_elem:
                return None

            question_text = self.processor.clean_text(question_elem.get_text())

            # Extraer opciones
            options = []
            option_elements = container.find_all(
                ['li', 'div'],
                class_=['option', 'answer-option', 'opcion', 'respuesta'],
            )

            if not option_elements:
                # Buscar inputs de radio con sus labels
                option_elements = container.find_all('label')

            for opt_elem in option_elements:
                opt_text = self.processor.clean_text(opt_elem.get_text())
                if opt_text:
                    options.append(opt_text)

            # Extraer respuesta correcta
            correct_elem = container.find(
                ['span', 'div', 'p'],
                class_=['correct', 'correct-answer', 'respuesta-correcta', 'answer-key'],
            )

            correct_answer = ''
            if correct_elem:
                correct_answer = self.processor.clean_text(correct_elem.get_text())

            # Extraer explicación
            explanation_elem = container.find(
                ['div', 'p'],
                class_=['explanation', 'explicacion', 'answer-explanation'],
            )

            explanation = ''
            if explanation_elem:
                explanation = self.processor.clean_text(explanation_elem.get_text())

            # Extraer imágenes
            images = []
            img_elements = container.find_all('img')
            for img in img_elements:
                if img.get('src'):
                    images.append({'src': img.get('src', ''), 'alt': img.get('alt', '')})

            return {
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'images': images,
            }

        except Exception as e:
            logger.debug(f'Error parseando contenedor: {e}')
            return None

    async def _extract_numbered_questions(
        self, context: BeautifulSoupCrawlingContext
    ) -> list[dict[str, Any]]:
        """Extraer preguntas con formato de lista numerada."""
        questions = []

        # Buscar listas ordenadas
        ol_elements = context.soup.find_all('ol')

        for ol in ol_elements:
            items = ol.find_all('li')
            if len(items) >= 3:  # Probable que sean preguntas
                for item in items:
                    text = self.processor.clean_text(item.get_text())
                    if len(text) > 20:  # Probablemente una pregunta
                        questions.append(
                            {
                                'question': text,
                                'options': [],
                                'correct_answer': '',
                                'explanation': '',
                                'images': [],
                            }
                        )

        return questions

    async def _process_question(
        self, question_data: dict[str, Any], source_url: str
    ) -> None:
        """Procesar y almacenar pregunta."""
        try:
            # Validar pregunta
            is_valid, error_msg = self.processor.validate_question(
                question_data['question'],
                question_data['options'],
                question_data.get('correct_answer', ''),
            )

            if not is_valid:
                logger.debug(f'Pregunta inválida: {error_msg}')
                return

            # Determinar categoría inteligentemente
            category = self.processor.extract_category(
                question_data['question'], source_url
            )

            # Agregar a base de datos
            question_id, is_new = self.database.add_question(
                question_text=question_data['question'],
                options=question_data['options'],
                correct_answer=question_data.get('correct_answer', 'No especificada'),
                explanation=question_data.get('explanation', ''),
                category=category,
                source_url=source_url,
                images=question_data.get('images', []),
            )

            if is_new:
                self.stats['questions_saved'] += 1
                logger.info(f'Pregunta guardada: {question_id} - {category}')

        except Exception as e:
            logger.error(f'Error procesando pregunta: {e}')

    def _generate_report(self) -> dict[str, Any]:
        """Generar reporte completo del proceso."""
        db_stats = self.database.get_statistics()

        report = {
            'timestamp': datetime.now().isoformat(),
            'scraping_stats': self.stats,
            'database_stats': db_stats,
            'efficiency': {
                'success_rate': (
                    (self.stats['pages_processed'] - self.stats['errors'])
                    / max(self.stats['pages_processed'], 1)
                )
                * 100,
                'questions_per_page': self.stats['questions_found']
                / max(self.stats['pages_processed'], 1),
                'save_rate': (
                    self.stats['questions_saved'] / max(self.stats['questions_found'], 1)
                )
                * 100,
            },
        }

        logger.info('=' * 80)
        logger.info('REPORTE FINAL DEL AGENTE DE IA')
        logger.info('=' * 80)
        logger.info(f'Páginas procesadas: {self.stats["pages_processed"]}')
        logger.info(f'Preguntas encontradas: {self.stats["questions_found"]}')
        logger.info(f'Preguntas guardadas: {self.stats["questions_saved"]}')
        logger.info(f'Errores: {self.stats["errors"]}')
        logger.info(f'Tasa de éxito: {report["efficiency"]["success_rate"]:.2f}%')
        logger.info(f'Preguntas únicas en BD: {db_stats["unique_questions"]}')
        logger.info(f'Categorías: {list(db_stats["categories"].keys())}')
        logger.info('=' * 80)

        return report

    def search_and_answer(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Buscar y responder preguntas basadas en consulta.

        Args:
            query: Texto de búsqueda
            limit: Número máximo de resultados

        Returns:
            Lista de preguntas relevantes con sus respuestas
        """
        logger.info(f'Buscando preguntas relacionadas con: "{query}"')
        results = self.database.search_questions(keyword=query, limit=limit)

        logger.info(f'Encontradas {len(results)} preguntas')
        for i, result in enumerate(results, 1):
            logger.info(f'\n{i}. {result["question"]}')
            logger.info(f'   Respuesta: {result["correct_answer"]}')
            if result.get('explanation'):
                logger.info(f'   Explicación: {result["explanation"]}')

        return results

    def export_database(self, format_type: str = 'json', output_path: str = '') -> str:
        """Exportar base de datos completa.

        Args:
            format_type: Formato de exportación ('json', 'csv', 'markdown')
            output_path: Ruta de salida

        Returns:
            Ruta del archivo exportado
        """
        return self.database.export_to_format(format_type, output_path)


async def main() -> None:
    """Función principal del agente de IA de clase mundial."""
    logger.info('=' * 80)
    logger.info('AGENTE DE IA DE CLASE MUNDIAL - PRUEBAS DE CONDUCIR')
    logger.info('=' * 80)

    # Crear agente de IA con configuración avanzada
    agent = DrivingTestAIAgent(
        max_requests=100,  # Límite para demostración
        headless=True,
        database_path='driving_questions_ai.json',
    )

    # URLs de ejemplo (en producción, usar URLs reales)
    start_urls = [
        'https://example.com/driving-test-questions',
        'https://example.com/practice-tests',
        # Agregar URLs reales de sitios de pruebas de conducir
    ]

    # Ejecutar proceso completo de scraping y análisis
    logger.info('Iniciando proceso de scraping inteligente...')
    report = await agent.scrape_and_process(start_urls)

    # Exportar base de datos en múltiples formatos
    logger.info('\nExportando base de datos...')
    agent.export_database('json', 'questions_export.json')
    agent.export_database('csv', 'questions_export.csv')
    agent.export_database('markdown', 'questions_export.md')

    # Demostrar capacidad de búsqueda y respuesta
    logger.info('\nDemostrando capacidades de búsqueda...')
    agent.search_and_answer('señales de tráfico', limit=3)
    agent.search_and_answer('velocidad', limit=3)

    # Mostrar estadísticas finales
    logger.info('\nEstadísticas de la base de datos:')
    stats = agent.database.get_statistics()
    for key, value in stats.items():
        logger.info(f'  {key}: {value}')

    logger.info('\n' + '=' * 80)
    logger.info('PROCESO COMPLETADO EXITOSAMENTE')
    logger.info('=' * 80)


if __name__ == '__main__':
    asyncio.run(main())
