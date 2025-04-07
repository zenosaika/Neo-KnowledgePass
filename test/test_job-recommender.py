import pytest
import os # Standard library for interacting with the operating system (e.g., file paths)
import time # Standard library for time-related functions (e.g., sleep)

# Selenium WebDriver components for browser automation
from selenium import webdriver
from selenium.webdriver.common.by import By # For locating elements using different strategies
from selenium.webdriver.support.ui import WebDriverWait # For waiting until certain conditions are met
from selenium.webdriver.support import expected_conditions as EC # Predefined conditions for WebDriverWait

# Specific Selenium exceptions for more granular error handling
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException

# --- Configuration ---

# Base URL for the application under test. Ensure this points to your running instance.
BASE_URL = "http://127.0.0.1:8000/"

# Default wait time (in seconds) for elements to appear or become interactive.
TIMEOUT = 10 # Adjusted from 3s for potentially slower loads or dynamic content

# Specific timeout (in seconds) after submitting the form, allowing for backend processing and page load.
SUBMIT_TIMEOUT = 20 # Adjusted from 3s, as results page generation might take longer

# --- WebDriver Fixture ---

@pytest.fixture
def browser():
    """
    Sets up and tears down the Safari WebDriver for each test function.
    Leverages pytest fixtures for cleaner setup/teardown logic.
    """
    # Initialize Safari WebDriver options (can be customized if needed)
    options = webdriver.SafariOptions()

    # Initialize the Safari driver instance
    # Note: Ensure Safari's 'Allow Remote Automation' is enabled in Develop menu.
    driver = webdriver.Safari(options=options)

    # Maximize the browser window for consistency
    driver.maximize_window()

    # 'yield' passes the driver instance to the test function
    yield driver

    # Teardown: Quit the driver after the test function completes
    driver.quit()

# --- Test Cases ---

def test_page_loads_successfully(browser):
    """Verifies that the main application page loads and has the expected title."""
    try:
        browser.get(BASE_URL)
        # Wait until the page title contains "Knowledge Pass"
        WebDriverWait(browser, TIMEOUT).until(EC.title_contains("Knowledge Pass"))
        # Assert that the full title matches exactly
        assert "Knowledge Pass - Personalized Internships" in browser.title
        print(f"\nPASS: Page loaded successfully (Title: '{browser.title}')")
    except TimeoutException:
        print(f"\nFAIL: Timed out waiting for page title on {BASE_URL}.")
        pytest.fail(f"Timed out waiting for page title on {BASE_URL}.")
    except Exception as e:
        print(f"\nFAIL: An unexpected error occurred during page load: {e}")
        pytest.fail(f"An unexpected error occurred during page load: {e}")


def test_course_tags_are_displayed(browser):
    """Checks if the course selection tags are present and visible on the page."""
    try:
        browser.get(BASE_URL)
        # Wait for the container holding the course tags to be present
        WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((By.ID, "courses-tag-area")))
        # Find all elements matching the tag selector within the container
        course_tags = browser.find_elements(By.CSS_SELECTOR, "#courses-tag-area .tag")
        # Ensure at least one tag was found
        assert course_tags, "No course tags were found within #courses-tag-area."
        # Verify that the first few tags are actually displayed (performance optimization)
        assert all(tag.is_displayed() for tag in course_tags[:5]), "Not all sample course tags were visible."
        print(f"\nPASS: Course tags are displayed ({len(course_tags)} found).")
    except TimeoutException:
        print("\nFAIL: Timed out waiting for the course tags area to load.")
        pytest.fail("Timed out waiting for the course tags area to load.")
    except AssertionError as e:
        print(f"\nFAIL: Assertion failed while checking course tags: {e}")
        pytest.fail(f"Assertion failed while checking course tags: {e}")
    except Exception as e:
        print(f"\nFAIL: An unexpected error occurred while checking course tags: {e}")
        pytest.fail(f"An unexpected error occurred while checking course tags: {e}")


def test_skill_tags_are_displayed(browser):
    """Checks if the skill selection tags are present and visible on the page."""
    try:
        browser.get(BASE_URL)
        # Wait for the container holding the skill tags
        WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((By.ID, "skills-tag-area")))
        # Find all skill tags within their container
        skill_tags = browser.find_elements(By.CSS_SELECTOR, "#skills-tag-area .tag")
        # Ensure tags were found
        assert skill_tags, "No skill tags were found within #skills-tag-area."
        # Check visibility of the first few tags
        assert all(tag.is_displayed() for tag in skill_tags[:5]), "Not all sample skill tags were visible."
        print(f"\nPASS: Skill tags are displayed ({len(skill_tags)} found).")
    except TimeoutException:
        print("\nFAIL: Timed out waiting for the skill tags area to load.")
        pytest.fail("Timed out waiting for the skill tags area to load.")
    except AssertionError as e:
        print(f"\nFAIL: Assertion failed while checking skill tags: {e}")
        pytest.fail(f"Assertion failed while checking skill tags: {e}")
    except Exception as e:
        print(f"\nFAIL: An unexpected error occurred while checking skill tags: {e}")
        pytest.fail(f"An unexpected error occurred while checking skill tags: {e}")


def test_course_tag_selection_updates_ui(browser):
    """Verifies that clicking a course tag adds the 'active' class, indicating selection."""
    try:
        browser.get(BASE_URL)
        # Wait for course tags and get them
        WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((By.ID, "courses-tag-area")))
        course_tags = browser.find_elements(By.CSS_SELECTOR, "#courses-tag-area .tag")
        assert course_tags, "Cannot test selection: No course tags found."

        # Select the first tag for the test
        first_tag = course_tags[0]
        tag_text = first_tag.text # Get text for logging

        # Using JavaScript click as it's often more robust for elements with event listeners
        browser.execute_script("arguments[0].click();", first_tag)

        # Explicitly wait until the 'active' class is present in the element's class list
        WebDriverWait(browser, TIMEOUT).until(
            lambda driver: first_tag.get_attribute("class") and "active" in first_tag.get_attribute("class").split()
        )

        # Assert the 'active' class is indeed present
        assert "active" in first_tag.get_attribute("class").split()
        print(f"\nPASS: Course tag '{tag_text}' successfully marked as active after click.")

    except TimeoutException:
        tag_text_for_error = "the first course tag"
        try: tag_text_for_error = f"course tag '{course_tags[0].text}'" # Attempt to get text for better error message
        except: pass
        print(f"\nFAIL: Timed out waiting for 'active' class to appear on {tag_text_for_error}.")
        pytest.fail(f"Timed out waiting for 'active' class on {tag_text_for_error}.")
    except AssertionError as e:
        print(f"\nFAIL: Assertion failed during course tag selection UI check: {e}")
        pytest.fail(f"Assertion failed during course tag selection UI check: {e}")
    except Exception as e:
        print(f"\nFAIL: An unexpected error occurred during course tag selection: {e}")
        pytest.fail(f"An unexpected error occurred during course tag selection: {e}")


def test_skill_tag_selection_updates_ui(browser):
    """Verifies that clicking a skill tag adds the 'active' class, indicating selection."""
    try:
        browser.get(BASE_URL)
        # Wait for skill tags and get them
        WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((By.ID, "skills-tag-area")))
        skill_tags = browser.find_elements(By.CSS_SELECTOR, "#skills-tag-area .tag")
        assert skill_tags, "Cannot test selection: No skill tags found."

        # Select the first skill tag
        first_tag = skill_tags[0]
        tag_text = first_tag.text

        # Use JavaScript click for reliability
        browser.execute_script("arguments[0].click();", first_tag)

        # Wait for the 'active' class confirmation
        WebDriverWait(browser, TIMEOUT).until(
            lambda driver: first_tag.get_attribute("class") and "active" in first_tag.get_attribute("class").split()
        )

        # Assert the class was added
        assert "active" in first_tag.get_attribute("class").split()
        print(f"\nPASS: Skill tag '{tag_text}' successfully marked as active after click.")

    except TimeoutException:
        tag_text_for_error = "the first skill tag"
        try: tag_text_for_error = f"skill tag '{skill_tags[0].text}'"
        except: pass
        print(f"\nFAIL: Timed out waiting for 'active' class to appear on {tag_text_for_error}.")
        pytest.fail(f"Timed out waiting for 'active' class on {tag_text_for_error}.")
    except AssertionError as e:
        print(f"\nFAIL: Assertion failed during skill tag selection UI check: {e}")
        pytest.fail(f"Assertion failed during skill tag selection UI check: {e}")
    except Exception as e:
        print(f"\nFAIL: An unexpected error occurred during skill tag selection: {e}")
        pytest.fail(f"An unexpected error occurred during skill tag selection: {e}")


def test_deselecting_course_tag_updates_ui(browser):
    """Verifies clicking an active course tag removes the 'active' class."""
    try:
        browser.get(BASE_URL)
        # Locate course tags
        WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((By.ID, "courses-tag-area")))
        course_tags = browser.find_elements(By.CSS_SELECTOR, "#courses-tag-area .tag")
        assert course_tags, "Cannot test deselection: No course tags found."

        first_tag = course_tags[0]
        tag_text = first_tag.text

        # First click: Select the tag
        browser.execute_script("arguments[0].click();", first_tag)
        # Wait to ensure it became active
        WebDriverWait(browser, TIMEOUT).until(
             lambda driver: first_tag.get_attribute("class") and "active" in first_tag.get_attribute("class").split()
        )

        # Second click: Deselect the tag
        browser.execute_script("arguments[0].click();", first_tag)

        # Wait for the 'active' class to be removed
        WebDriverWait(browser, TIMEOUT).until(
             lambda driver: first_tag.get_attribute("class") and "active" not in first_tag.get_attribute("class").split()
        )

        # Assert the 'active' class is no longer present
        assert "active" not in first_tag.get_attribute("class").split()
        print(f"\nPASS: Course tag '{tag_text}' successfully deselected (active class removed).")

    except TimeoutException:
         tag_text_for_error = "the first course tag"
         try: tag_text_for_error = f"course tag '{course_tags[0].text}'"
         except: pass
         print(f"\nFAIL: Timed out waiting for 'active' class removal on {tag_text_for_error}.")
         pytest.fail(f"Timed out waiting for 'active' class removal on {tag_text_for_error}.")
    except AssertionError as e:
        print(f"\nFAIL: Assertion failed during course tag deselection UI check: {e}")
        pytest.fail(f"Assertion failed during course tag deselection UI check: {e}")
    except Exception as e:
        print(f"\nFAIL: An unexpected error occurred during course tag deselection: {e}")
        pytest.fail(f"An unexpected error occurred during course tag deselection: {e}")


def test_deselecting_skill_tag_updates_ui(browser):
    """Verifies clicking an active skill tag removes the 'active' class."""
    try:
        browser.get(BASE_URL)
        # Locate skill tags
        WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((By.ID, "skills-tag-area")))
        skill_tags = browser.find_elements(By.CSS_SELECTOR, "#skills-tag-area .tag")
        assert skill_tags, "Cannot test deselection: No skill tags found."

        first_tag = skill_tags[0]
        tag_text = first_tag.text

        # First click: Select
        browser.execute_script("arguments[0].click();", first_tag)
        # Wait for active state
        WebDriverWait(browser, TIMEOUT).until(
            lambda driver: first_tag.get_attribute("class") and "active" in first_tag.get_attribute("class").split()
        )

        # Second click: Deselect
        browser.execute_script("arguments[0].click();", first_tag)

        # Wait for inactive state
        WebDriverWait(browser, TIMEOUT).until(
            lambda driver: first_tag.get_attribute("class") and "active" not in first_tag.get_attribute("class").split()
        )

        # Assert class is removed
        assert "active" not in first_tag.get_attribute("class").split()
        print(f"\nPASS: Skill tag '{tag_text}' successfully deselected (active class removed).")

    except TimeoutException:
         tag_text_for_error = "the first skill tag"
         try: tag_text_for_error = f"skill tag '{skill_tags[0].text}'"
         except: pass
         print(f"\nFAIL: Timed out waiting for 'active' class removal on {tag_text_for_error}.")
         pytest.fail(f"Timed out waiting for 'active' class removal on {tag_text_for_error}.")
    except AssertionError as e:
        print(f"\nFAIL: Assertion failed during skill tag deselection UI check: {e}")
        pytest.fail(f"Assertion failed during skill tag deselection UI check: {e}")
    except Exception as e:
        print(f"\nFAIL: An unexpected error occurred during skill tag deselection: {e}")
        pytest.fail(f"An unexpected error occurred during skill tag deselection: {e}")


def test_submit_button_is_enabled(browser):
    """Confirms the main submission button is present and enabled on page load."""
    try:
        browser.get(BASE_URL)
        # Wait specifically for the button to be clickable (implies presence, visibility, and enabled state)
        submit_button = WebDriverWait(browser, TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "recommendation-button"))
        )
        # Double-check the enabled state directly (though EC.element_to_be_clickable should cover it)
        assert submit_button.is_enabled()
        print("\nPASS: Submit button is present and enabled.")
    except TimeoutException:
        print("\nFAIL: Timed out waiting for the submit button to become clickable.")
        pytest.fail("Timed out waiting for the submit button to become clickable.")
    except AssertionError:
        print("\nFAIL: Submit button was found but was not enabled.")
        pytest.fail("Submit button was found but was not enabled.")
    except Exception as e:
        print(f"\nFAIL: An unexpected error occurred checking the submit button: {e}")
        pytest.fail(f"An unexpected error occurred checking the submit button: {e}")


def test_error_message_is_initially_hidden(browser):
    """Ensures the form validation error message area is initially hidden."""
    try:
        browser.get(BASE_URL)
        # Wait for the error message container to be present in the DOM
        error_message = WebDriverWait(browser, TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "form-error"))
        )
        # Check if the 'hidden' class is present, indicating it's not visible
        assert "hidden" in error_message.get_attribute("class")
        print("\nPASS: Form error message area is initially hidden.")
    except TimeoutException:
        print("\nFAIL: Timed out waiting for the form error message element.")
        pytest.fail("Timed out waiting for the form error message element.")
    except AssertionError:
        print("\nFAIL: Form error message area was not hidden on initial load.")
        pytest.fail("Form error message area was not hidden on initial load.")
    except Exception as e:
        print(f"\nFAIL: An unexpected error occurred checking the error message: {e}")
        pytest.fail(f"An unexpected error occurred checking the error message: {e}")


def test_knowledge_pass_link_navigates_home(browser):
    """Verifies clicking the main 'Knowledge Pass' brand link in the navbar returns to the homepage."""
    # Start on the base page (or potentially navigate away first if needed)
    browser.get(BASE_URL)

    try:
        # Locate the main brand link in the navigation bar
        knowledge_pass_link = WebDriverWait(browser, TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//nav//a[contains(text(), 'Knowledge Pass')]"))
        )
        # Click the link
        knowledge_pass_link.click()

        # Wait for the URL to potentially reload or confirm it's the base URL
        WebDriverWait(browser, TIMEOUT).until(EC.url_to_be(BASE_URL))

        # Assert the current URL is the expected homepage URL
        assert browser.current_url == BASE_URL
        print(f"\nPASS: Knowledge Pass link click correctly navigated to homepage ({browser.current_url}).")
    except TimeoutException:
         print(f"\nFAIL: Timed out waiting for navigation to home via Knowledge Pass link. Current URL: {browser.current_url}")
         pytest.fail("Timed out waiting for navigation to home.")
    except AssertionError:
         print(f"\nFAIL: Navigation via Knowledge Pass link failed. Expected: {BASE_URL}, Actual: {browser.current_url}")
         pytest.fail("Navigation via Knowledge Pass link failed.")
    except Exception as e:
         print(f"\nFAIL: An error occurred during Knowledge Pass link navigation: {e}")
         pytest.fail(f"An error occurred during Knowledge Pass link navigation: {e}")


def test_select_tags_and_submit_navigates_to_results(browser):
    """
    Simulates selecting a course and skill, submitting the form,
    and verifying successful navigation to the results/visualization page.
    """
    try:
        print("\nINFO: Starting test_select_tags_and_submit_navigates_to_results...")
        browser.get(BASE_URL)

        # --- Step 1: Select a Course Tag ---
        print("INFO: Locating and selecting a course tag...")
        WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((By.ID, "courses-tag-area")))
        course_tags = browser.find_elements(By.CSS_SELECTOR, "#courses-tag-area .tag")
        assert course_tags, "Cannot proceed: No course tags found to select."
        # Choose a specific tag (e.g., the second one)
        course_to_select = course_tags[1]
        course_text = course_to_select.text
        browser.execute_script("arguments[0].click();", course_to_select)
        print(f"INFO: Selected course: '{course_text}'")

        # --- Step 2: Select a Skill Tag ---
        print("INFO: Locating and selecting a skill tag...")
        WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((By.ID, "skills-tag-area")))
        skill_tags = browser.find_elements(By.CSS_SELECTOR, "#skills-tag-area .tag")
        assert skill_tags, "Cannot proceed: No skill tags found to select."
        # Choose a specific tag (e.g., the third one)
        skill_to_select = skill_tags[2]
        skill_text = skill_to_select.text
        browser.execute_script("arguments[0].click();", skill_to_select)
        print(f"INFO: Selected skill: '{skill_text}'")

        # --- Step 3: Find and Click Submit Button ---
        print("INFO: Locating and clicking the submit button...")
        submit_button = WebDriverWait(browser, TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "recommendation-button"))
        )
        # Scrolling into view helps ensure the button isn't obscured by other elements
        browser.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        # Using JavaScript click as a robust method against potential interactability issues
        browser.execute_script("arguments[0].click();", submit_button)
        print("INFO: Clicked submit button via JavaScript.")

        # --- Step 4: Wait for Navigation to Visualization Page ---
        expected_url = BASE_URL + "visualization/" # Assumes '/visualization/' is the target path
        print(f"INFO: Waiting up to {SUBMIT_TIMEOUT}s for navigation to: {expected_url}")
        # Wait until the browser's current URL matches the expected results page URL
        WebDriverWait(browser, SUBMIT_TIMEOUT).until(EC.url_to_be(expected_url))
        print(f"INFO: Successfully navigated to URL: {browser.current_url}")

        # --- Step 5: Verify Visualization Page Loaded (URL and Title) ---
        print("INFO: Verifying results page content...")
        assert browser.current_url == expected_url, f"URL mismatch. Expected: {expected_url}, Actual: {browser.current_url}"
        # Wait for the title of the results page to be present
        WebDriverWait(browser, TIMEOUT).until(EC.title_contains("Results"))
        assert "Knowledge Pass - Results" in browser.title, f"Incorrect page title: '{browser.title}'"
        print(f"INFO: Results page title is correct: '{browser.title}'")

        # --- Step 6: Verify Key Content Element ---
        # As an additional check, wait for a core element (like the main heading) to ensure the page rendered
        WebDriverWait(browser, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".page-title"))
        )
        assert browser.find_element(By.CSS_SELECTOR, ".page-title").is_displayed(), "Results page title element not visible."
        print("INFO: Results page main title element found and is visible.")

        print(f"\nPASS: Successfully selected tags ('{course_text}', '{skill_text}'), submitted, and verified navigation to results page.")

    except TimeoutException as e:
        current_url = browser.current_url
        print(f"\nFAIL: Timed out during test execution. Current URL: {current_url}.")
        print(f"Error Details: {e}")
        # Attempt to grab page source or screenshot for better debugging if possible
        try:
            body_start = browser.find_element(By.TAG_NAME, 'body').text[:500] # Capture beginning of body text
            print(f"DEBUG: Current page body (start): {body_start}...")
        except:
             print("DEBUG: Could not retrieve page body text.")
        pytest.fail(f"Timed out. Current URL: {current_url}. Check logs/console. Error: {e}")

    except ElementNotInteractableException as e:
        current_url = browser.current_url
        print(f"\nFAIL: Element not interactable error encountered. Current URL: {current_url}.")
        print(f"Error Details: {e}")
        try:
            # Check button's state when the error occurred
            button_displayed = browser.find_element(By.ID, "recommendation-button").is_displayed()
            print(f"DEBUG: Is submit button displayed during error?: {button_displayed}")
        except:
            print("DEBUG: Could not check submit button display state during error.")
        pytest.fail(f"Element not interactable. Current URL: {current_url}. Error: {e}")

    except AssertionError as e:
        print(f"\nFAIL: Assertion failed during test execution: {e}")
        pytest.fail(f"Assertion failed: {e}")

    except Exception as e:
        current_url = browser.current_url
        print(f"\nFAIL: An unexpected error occurred at URL {current_url}: {e}")
        pytest.fail(f"An unexpected error occurred: {e}")


# --- Test Runner ---
if __name__ == "__main__":
    # Executes the tests within this file using pytest when run directly.
    # Flags: -v (verbose output), -s (show print statements during execution)
    print("Starting test execution...")
    pytest.main([__file__, '-v', '-s'])
    print("Test execution finished.")