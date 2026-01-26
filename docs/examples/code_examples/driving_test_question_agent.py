import asyncio

from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext


async def main() -> None:
    """Agent that scrapes and answers driving test questions.

    This example demonstrates how to create an agent that can:
    1. Scrape driving test questions from websites
    2. Extract question text, options, and correct answers
    3. Store the data in a structured format for future reference

    This is useful for creating study materials or practice tests.
    """
    # Create a crawler instance optimized for scraping driving test content
    crawler = BeautifulSoupCrawler(
        # Limit requests during testing, remove for full crawling
        max_requests_per_crawl=50,
        # Retry failed requests
        max_request_retries=2,
    )

    # Define the request handler to extract driving test questions
    @crawler.router.default_handler
    async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
        """Extract driving test questions and answers from the page."""
        context.log.info(f'Processing {context.request.url} ...')

        # Extract all questions from the page
        # This is a generic example - adjust selectors based on actual website structure
        questions = context.soup.find_all('div', class_='question')

        for idx, question_element in enumerate(questions, 1):
            # Extract question text
            question_text_elem = question_element.find('p', class_='question-text')
            if not question_text_elem:
                question_text_elem = question_element.find('h3')

            if question_text_elem:
                question_text = question_text_elem.get_text(strip=True)
            else:
                continue

            # Extract options (typically A, B, C, D)
            options = []
            option_elements = question_element.find_all('li', class_='option')
            if not option_elements:
                # Try alternative structure
                option_elements = question_element.find_all('div', class_='answer-option')

            for option in option_elements:
                option_text = option.get_text(strip=True)
                options.append(option_text)

            # Extract the correct answer
            correct_answer_elem = question_element.find('span', class_='correct-answer')
            if not correct_answer_elem:
                correct_answer_elem = question_element.find('div', class_='answer')

            if correct_answer_elem:
                correct_answer = correct_answer_elem.get_text(strip=True)
            else:
                correct_answer = 'Not specified'

            # Extract explanation if available
            explanation_elem = question_element.find('div', class_='explanation')
            explanation = (
                explanation_elem.get_text(strip=True) if explanation_elem else ''
            )

            # Structure the data
            question_data = {
                'question_number': idx,
                'url': context.request.url,
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation,
            }

            # Store the extracted data
            await context.push_data(question_data)
            context.log.info(f'Extracted question {idx}: {question_text[:50]}...')

        # Find and enqueue links to more questions
        # Look for pagination or related question pages
        await context.enqueue_links(
            selector='a.next-page, a.more-questions, nav.pagination a',
        )

    # Run the crawler with initial URLs
    # Replace these with actual driving test question websites
    # Examples could include official DMV practice tests or educational sites
    await crawler.run(
        [
            'https://example.com/driving-test-questions',
            # Add more URLs as needed
        ]
    )


if __name__ == '__main__':
    asyncio.run(main())
