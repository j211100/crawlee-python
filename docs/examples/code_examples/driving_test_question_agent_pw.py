import asyncio

from playwright.async_api import Page

from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext


async def main() -> None:
    """Interactive agent for driving test questions using Playwright.

    This example demonstrates how to create an agent that can:
    1. Navigate JavaScript-heavy driving test websites
    2. Interact with interactive quizzes and tests
    3. Extract questions, select answers, and verify results
    4. Store comprehensive test data

    Use this when dealing with dynamic websites that require browser interaction.
    """
    # Create a Playwright crawler for JavaScript-heavy sites
    crawler = PlaywrightCrawler(
        # Limit requests during testing
        max_requests_per_crawl=20,
        # Set to False to see browser in action (useful for debugging)
        headless=True,
        # Retry failed requests
        max_request_retries=2,
    )

    # Define the request handler for interactive test pages
    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        """Handle interactive driving test pages."""
        context.log.info(f'Processing {context.request.url} ...')

        # Wait for the page to load completely
        await context.page.wait_for_load_state('networkidle')

        # Example: Extract questions from an interactive quiz
        # Adjust selectors based on the actual website structure

        # Find all question containers
        questions = await context.page.query_selector_all(
            '.quiz-question, .test-question'
        )

        for idx, question_element in enumerate(questions, 1):
            # Extract question text
            question_text = await question_element.query_selector('.question-text, h3')
            if question_text:
                question_text = await question_text.inner_text()
            else:
                continue

            # Extract answer options
            options = []
            option_elements = await question_element.query_selector_all(
                '.answer-option, .option, input[type="radio"] + label'
            )

            for option_elem in option_elements:
                option_text = await option_elem.inner_text()
                options.append(option_text.strip())

            # Try to find the correct answer (if revealed)
            correct_answer = ''
            correct_elem = await question_element.query_selector('.correct, .answer-key')
            if correct_elem:
                correct_answer = await correct_elem.inner_text()

            # Check if there's an explanation
            explanation = ''
            explanation_elem = await question_element.query_selector(
                '.explanation, .answer-explanation'
            )
            if explanation_elem:
                explanation = await explanation_elem.inner_text()

            # Extract any images (like traffic signs)
            images = []
            image_elements = await question_element.query_selector_all('img')
            for img in image_elements:
                img_src = await img.get_attribute('src')
                img_alt = await img.get_attribute('alt')
                if img_src:
                    images.append({'src': img_src, 'alt': img_alt or ''})

            # Structure the data
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

            # Store the extracted data
            await context.push_data(question_data)
            context.log.info(f'Extracted question {idx}: {question_text[:50]}...')

        # Look for "Next" or "Continue" buttons to navigate to more questions
        try:
            next_button = await context.page.query_selector(
                'button.next, a.next-page, button:has-text("Next"), '
                'button:has-text("Continue")'
            )
            if next_button:
                next_url = await next_button.get_attribute('href')
                if next_url:
                    await context.enqueue_links(selector='button.next, a.next-page')
        except Exception:  # noqa: S110
            # Expected: Not all pages have next buttons
            pass

        # Enqueue links to other test categories or question sets
        await context.enqueue_links(
            selector='a[href*="test"], a[href*="quiz"], a[href*="questions"]',
        )

    # Run the crawler with initial URLs
    # Replace with actual driving test websites
    await crawler.run(
        [
            'https://example.com/driving-test',
            # Add more URLs as needed
        ]
    )


async def extract_category(page: Page) -> str:
    """Extract the category/topic of the driving test questions."""
    try:
        # Try to find category information
        category_elem = await page.query_selector('.category, .topic, .test-category')
        if category_elem:
            return await category_elem.inner_text()

        # Try to extract from page title
        title = await page.title()
        if 'category' in title.lower() or 'topic' in title.lower():
            return title

    except Exception:
        # Return default category if extraction fails
        return 'General'

    return 'General'


if __name__ == '__main__':
    asyncio.run(main())
