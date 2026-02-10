#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          🚗 DEMOSTRACIÓN INTERACTIVA - AGENTE DE PRUEBAS DE CONDUCIR         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Esta demostración muestra las capacidades del sistema de agentes de IA
para pruebas de conducir sin necesidad de acceder a sitios web externos.

Ejecutar: python demo_driving_test_agent.py
"""

import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
#                             COLORES PARA TERMINAL
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    """Colores ANSI para terminal."""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header(text: str, color: str = Colors.CYAN) -> None:
    """Imprimir encabezado con estilo."""
    print(f"\n{color}{Colors.BOLD}{'═' * 70}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}  {text}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{'═' * 70}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Imprimir mensaje de éxito."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Imprimir información."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Imprimir advertencia."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
#                         BASE DE DATOS DE DEMOSTRACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class DemoQuestionDatabase:
    """Base de datos simplificada para demostración."""

    def __init__(self, db_path: str = 'demo_questions.json'):
        """Inicializar base de datos."""
        self.db_path = Path(db_path)
        self.questions: dict = {}
        self.stats = {
            'total_questions': 0,
            'unique_questions': 0,
            'categories': defaultdict(int),
        }
        self._load_database()

    def _load_database(self) -> None:
        """Cargar base de datos existente."""
        if self.db_path.exists():
            with open(self.db_path, encoding='utf-8') as f:
                data = json.load(f)
                self.questions = data.get('questions', {})
                stats_data = data.get('stats', {})
                self.stats['total_questions'] = stats_data.get('total_questions', 0)
                self.stats['unique_questions'] = stats_data.get('unique_questions', 0)
                cats = stats_data.get('categories', {})
                for k, v in cats.items():
                    self.stats['categories'][k] = v

    def _generate_id(self, text: str) -> str:
        """Generar ID único."""
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def add_question(
        self,
        question_text: str,
        options: list,
        correct_answer: str,
        explanation: str = '',
        category: str = 'General',
    ) -> tuple:
        """Agregar pregunta a la base de datos."""
        question_id = self._generate_id(question_text)
        is_new = question_id not in self.questions

        if is_new:
            self.questions[question_id] = {
                'id': question_id,
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'category': category,
                'created_at': datetime.now().isoformat(),
            }
            self.stats['unique_questions'] += 1
            self.stats['categories'][category] += 1

        self.stats['total_questions'] += 1
        return question_id, is_new

    def search(self, keyword: str, limit: int = 5) -> list:
        """Buscar preguntas por palabra clave."""
        results = []
        keyword_lower = keyword.lower()
        for q in self.questions.values():
            if keyword_lower in q['question'].lower():
                results.append(q)
                if len(results) >= limit:
                    break
        return results

    def get_by_category(self, category: str) -> list:
        """Obtener preguntas por categoría."""
        return [q for q in self.questions.values() if q['category'] == category]

    def save(self) -> None:
        """Guardar base de datos."""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump({
                'questions': self.questions,
                'stats': {
                    'total_questions': self.stats['total_questions'],
                    'unique_questions': self.stats['unique_questions'],
                    'categories': dict(self.stats['categories']),
                },
                'last_updated': datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)

    def get_stats(self) -> dict:
        """Obtener estadísticas."""
        return {
            'total': self.stats['total_questions'],
            'unique': self.stats['unique_questions'],
            'categories': dict(self.stats['categories']),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                      PREGUNTAS DE EJEMPLO PARA DEMOSTRACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

DEMO_QUESTIONS = [
    {
        'question': '¿Qué significa una señal de STOP?',
        'options': [
            'A) Reducir la velocidad',
            'B) Detenerse completamente',
            'C) Ceder el paso',
            'D) Precaución, peligro adelante',
        ],
        'correct': 'B) Detenerse completamente',
        'explanation': 'La señal de STOP indica que el conductor debe detenerse '
                       'completamente antes de continuar.',
        'category': 'Señales',
    },
    {
        'question': '¿Cuál es el límite de velocidad máximo en autopistas en España?',
        'options': [
            'A) 100 km/h',
            'B) 110 km/h',
            'C) 120 km/h',
            'D) 130 km/h',
        ],
        'correct': 'C) 120 km/h',
        'explanation': 'En España, el límite máximo de velocidad en autopistas '
                       'y autovías es de 120 km/h para turismos.',
        'category': 'Normativa',
    },
    {
        'question': '¿Con qué frecuencia se debe revisar la presión de los neumáticos?',
        'options': [
            'A) Una vez al año',
            'B) Cada 6 meses',
            'C) Al menos una vez al mes',
            'D) Solo cuando se nota que están desinflados',
        ],
        'correct': 'C) Al menos una vez al mes',
        'explanation': 'Se recomienda revisar la presión de los neumáticos al menos '
                       'una vez al mes y antes de viajes largos.',
        'category': 'Mecánica',
    },
    {
        'question': '¿Cuándo es obligatorio el uso del cinturón de seguridad?',
        'options': [
            'A) Solo en carretera',
            'B) Solo en asientos delanteros',
            'C) Siempre, para todos los ocupantes',
            'D) Solo cuando hay niños en el vehículo',
        ],
        'correct': 'C) Siempre, para todos los ocupantes',
        'explanation': 'El cinturón de seguridad es obligatorio para todos los '
                       'ocupantes del vehículo en cualquier tipo de vía.',
        'category': 'Seguridad',
    },
    {
        'question': '¿Qué distancia de seguridad se debe mantener con el vehículo de adelante?',
        'options': [
            'A) 2 metros',
            'B) Lo que se recorra en 2 segundos',
            'C) 10 metros',
            'D) 5 metros',
        ],
        'correct': 'B) Lo que se recorra en 2 segundos',
        'explanation': 'La regla de los 2 segundos permite mantener una distancia '
                       'segura adaptada a la velocidad.',
        'category': 'Conducción',
    },
    {
        'question': '¿Quién tiene prioridad en una rotonda?',
        'options': [
            'A) El que entra a la rotonda',
            'B) El que está dentro de la rotonda',
            'C) El que viene por la derecha',
            'D) El vehículo más grande',
        ],
        'correct': 'B) El que está dentro de la rotonda',
        'explanation': 'Los vehículos que circulan por la rotonda tienen prioridad '
                       'sobre los que pretenden entrar.',
        'category': 'Prioridad',
    },
    {
        'question': '¿Qué indica una luz amarilla fija del semáforo?',
        'options': [
            'A) Paso permitido',
            'B) Detenerse si es posible hacerlo de forma segura',
            'C) Acelerar para pasar',
            'D) Ceder el paso a peatones',
        ],
        'correct': 'B) Detenerse si es posible hacerlo de forma segura',
        'explanation': 'La luz amarilla indica que el semáforo cambiará a rojo. '
                       'Debe detenerse si puede hacerlo de forma segura.',
        'category': 'Señales',
    },
    {
        'question': '¿Cada cuántos kilómetros se debe cambiar el aceite del motor?',
        'options': [
            'A) Cada 5,000 km',
            'B) Entre 10,000 y 15,000 km según fabricante',
            'C) Cada 50,000 km',
            'D) Solo cuando el testigo se enciende',
        ],
        'correct': 'B) Entre 10,000 y 15,000 km según fabricante',
        'explanation': 'El intervalo de cambio de aceite varía según el fabricante '
                       'y tipo de aceite, generalmente entre 10,000 y 15,000 km.',
        'category': 'Mecánica',
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
#                            DEMOSTRACIÓN INTERACTIVA
# ═══════════════════════════════════════════════════════════════════════════════

def demo_add_questions(db: DemoQuestionDatabase) -> None:
    """Demostrar agregar preguntas a la base de datos."""
    print_header("📝 AGREGANDO PREGUNTAS A LA BASE DE DATOS", Colors.GREEN)

    for i, q in enumerate(DEMO_QUESTIONS, 1):
        qid, is_new = db.add_question(
            question_text=q['question'],
            options=q['options'],
            correct_answer=q['correct'],
            explanation=q['explanation'],
            category=q['category'],
        )
        status = "NUEVA" if is_new else "EXISTENTE"
        print(f"  {Colors.CYAN}{i}.{Colors.RESET} [{Colors.GREEN}{status}{Colors.RESET}] "
              f"{q['question'][:50]}...")
        print(f"     ID: {Colors.MAGENTA}{qid}{Colors.RESET} | "
              f"Categoría: {Colors.YELLOW}{q['category']}{Colors.RESET}")

    print()
    print_success(f"Se procesaron {len(DEMO_QUESTIONS)} preguntas")


def demo_search(db: DemoQuestionDatabase) -> None:
    """Demostrar búsqueda de preguntas."""
    print_header("🔍 BUSCANDO PREGUNTAS", Colors.BLUE)

    search_terms = ['velocidad', 'señal', 'cinturón']

    for term in search_terms:
        print(f"\n{Colors.BOLD}Buscando: \"{term}\"{Colors.RESET}")
        results = db.search(term, limit=3)

        if results:
            for r in results:
                print(f"  {Colors.GREEN}✓{Colors.RESET} {r['question']}")
                print(f"    Respuesta: {Colors.CYAN}{r['correct_answer']}{Colors.RESET}")
        else:
            print(f"  {Colors.YELLOW}No se encontraron resultados{Colors.RESET}")


def demo_categories(db: DemoQuestionDatabase) -> None:
    """Demostrar filtrado por categorías."""
    print_header("📂 PREGUNTAS POR CATEGORÍA", Colors.MAGENTA)

    stats = db.get_stats()
    categories = stats['categories']

    print(f"Total de categorías: {Colors.BOLD}{len(categories)}{Colors.RESET}\n")

    for category, count in sorted(categories.items()):
        emoji = {
            'Señales': '🛑',
            'Normativa': '📋',
            'Mecánica': '⚙️',
            'Seguridad': '🛡️',
            'Conducción': '🚗',
            'Prioridad': '🔀',
            'General': '📌',
        }.get(category, '📌')

        print(f"  {emoji} {Colors.CYAN}{category}{Colors.RESET}: "
              f"{Colors.GREEN}{count}{Colors.RESET} preguntas")

        # Mostrar una pregunta de ejemplo
        questions = db.get_by_category(category)
        if questions:
            print(f"     Ejemplo: {questions[0]['question'][:60]}...")


def demo_quiz(db: DemoQuestionDatabase) -> None:
    """Demostrar modo quiz interactivo."""
    print_header("🎯 MODO QUIZ - PRUEBA TUS CONOCIMIENTOS", Colors.YELLOW)

    # Seleccionar 3 preguntas para el quiz
    quiz_questions = list(db.questions.values())[:3]

    score = 0
    total = len(quiz_questions)

    for i, q in enumerate(quiz_questions, 1):
        print(f"\n{Colors.BOLD}Pregunta {i}/{total}:{Colors.RESET}")
        print(f"{Colors.CYAN}{q['question']}{Colors.RESET}\n")

        for opt in q['options']:
            print(f"  {opt}")

        # Simular respuesta del usuario (en demo, mostramos la correcta)
        print(f"\n{Colors.GREEN}✓ Respuesta correcta: {q['correct_answer']}{Colors.RESET}")

        if q['explanation']:
            print(f"{Colors.YELLOW}💡 Explicación: {q['explanation']}{Colors.RESET}")

        score += 1  # En demo, todas son "correctas"

    print(f"\n{Colors.BOLD}━━━ RESULTADO ━━━{Colors.RESET}")
    print(f"Puntuación: {Colors.GREEN}{score}/{total}{Colors.RESET} "
          f"({Colors.GREEN}{score/total*100:.0f}%{Colors.RESET})")


def demo_statistics(db: DemoQuestionDatabase) -> None:
    """Mostrar estadísticas de la base de datos."""
    print_header("📊 ESTADÍSTICAS DE LA BASE DE DATOS", Colors.CYAN)

    stats = db.get_stats()

    print(f"  {Colors.GREEN}●{Colors.RESET} Total de preguntas procesadas: "
          f"{Colors.BOLD}{stats['total']}{Colors.RESET}")
    print(f"  {Colors.GREEN}●{Colors.RESET} Preguntas únicas: "
          f"{Colors.BOLD}{stats['unique']}{Colors.RESET}")
    print(f"  {Colors.GREEN}●{Colors.RESET} Categorías: "
          f"{Colors.BOLD}{len(stats['categories'])}{Colors.RESET}")

    # Gráfico de barras simple
    print(f"\n{Colors.BOLD}Distribución por categoría:{Colors.RESET}")
    max_count = max(stats['categories'].values()) if stats['categories'] else 1
    for cat, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
        bar_len = int(count / max_count * 30)
        bar = '█' * bar_len + '░' * (30 - bar_len)
        print(f"  {cat:12} {Colors.CYAN}{bar}{Colors.RESET} {count}")


def demo_export(db: DemoQuestionDatabase) -> None:
    """Demostrar exportación de datos."""
    print_header("💾 EXPORTANDO DATOS", Colors.GREEN)

    # Exportar a JSON
    db.save()
    print_success(f"Base de datos guardada en: {db.db_path}")

    # Mostrar ejemplo del formato
    print(f"\n{Colors.BOLD}Ejemplo de formato JSON:{Colors.RESET}")
    if db.questions:
        sample = list(db.questions.values())[0]
        print(f"{Colors.CYAN}{json.dumps(sample, indent=2, ensure_ascii=False)[:500]}...{Colors.RESET}")


def main() -> None:
    """Función principal de demostración."""
    # Banner de inicio
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗    █████╗ ██╗                 ║
║   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝   ██╔══██╗██║                 ║
║   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗   ███████║██║                 ║
║   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║   ██╔══██║██║                 ║
║   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║   ██║  ██║██║                 ║
║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝  ╚═╝╚═╝                 ║
║                                                                              ║
║              🚗 AGENTE DE IA PARA PRUEBAS DE CONDUCIR 🚗                    ║
║                      DEMOSTRACIÓN INTERACTIVA                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}""")

    print(f"{Colors.WHITE}Esta demostración muestra las capacidades del sistema:{Colors.RESET}")
    print(f"  {Colors.GREEN}•{Colors.RESET} Agregar preguntas a la base de datos")
    print(f"  {Colors.GREEN}•{Colors.RESET} Búsqueda por palabras clave")
    print(f"  {Colors.GREEN}•{Colors.RESET} Filtrado por categorías")
    print(f"  {Colors.GREEN}•{Colors.RESET} Modo quiz interactivo")
    print(f"  {Colors.GREEN}•{Colors.RESET} Estadísticas y exportación")

    # Crear base de datos de demostración
    db = DemoQuestionDatabase('demo_driving_questions.json')

    # Ejecutar todas las demos
    demo_add_questions(db)
    demo_search(db)
    demo_categories(db)
    demo_quiz(db)
    demo_statistics(db)
    demo_export(db)

    # Mensaje final
    print(f"""
{Colors.GREEN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                     ✅ DEMOSTRACIÓN COMPLETADA CON ÉXITO                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  El sistema de agentes de IA para pruebas de conducir está funcionando      ║
║  correctamente. Puedes usar los siguientes archivos para más funcionalidad: ║
║                                                                              ║
║  📝 driving_test_question_agent.py     - Agente básico con BeautifulSoup    ║
║  🎭 driving_test_question_agent_pw.py  - Agente con Playwright              ║
║  🤖 driving_test_ai_agent_complete.py  - Agente IA completo                 ║
║  ⚡ driving_test_quantum_agent.py      - Agente cuántico avanzado           ║
║                                                                              ║
║  Base de datos guardada en: demo_driving_questions.json                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}""")


if __name__ == '__main__':
    main()
