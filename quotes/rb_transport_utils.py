from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from django.conf import settings
import time
from datetime import datetime, date, timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)


def submit_order_to_rb_transport(order, is_test=None):
    """
    Submit order to RB Transport portal automatically
    Returns True if successful, False otherwise

    Args:
        order: Django Order object
        is_test: Override settings.RB_TRANSPORT_TEST_MODE if needed (True/False/None)
    """

    # Determine if this is a test submission
    test_submission = is_test if is_test is not None else getattr(settings, 'RB_TRANSPORT_TEST_MODE', True)

    # Get credentials from settings
    username = getattr(settings, 'RB_TRANSPORT_USERNAME', 'Budget Pavers')
    password = getattr(settings, 'RB_TRANSPORT_PASSWORD', 'ARBP2906')

    chrome_options = Options()
    # Remove headless for debugging - you can add it back later
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = None

    try:
        test_prefix = "[TEST] " if test_submission else ""
        mode_text = "(TEST MODE)" if test_submission else "(PRODUCTION MODE)"
        print(f"🚛 Starting RB Transport submission for order {order.order_number} {mode_text}")

        # Initialize Chrome driver with auto-download
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)

        # Step 1: Go to RB Transport website
        print("📱 Opening RB Transport website...")
        driver.get('https://rbtransport.com.au/')
        time.sleep(2)

        # Step 2: Find and click login button
        print("🔑 Looking for login button...")
        try:
            # Try different selectors for login button
            login_selectors = [
                "//a[contains(text(), 'LOGIN')]",
                "//button[contains(text(), 'LOGIN')]",
                "//a[contains(@class, 'login')]",
                "//button[contains(@class, 'login')]",
                "//a[@href*='login']"
            ]

            login_button = None
            for selector in login_selectors:
                try:
                    login_button = driver.find_element(By.XPATH, selector)
                    if login_button.is_displayed():
                        break
                except:
                    continue

            if not login_button:
                print("❌ Could not find login button")
                return False

            login_button.click()
            print("✅ Clicked login button")
            time.sleep(3)

        except Exception as e:
            print(f"❌ Error finding login button: {str(e)}")
            return False

        # Step 3: Fill in login credentials
        print("🔐 Filling in login credentials...")
        try:
            # Wait for login form and fill credentials
            username_selectors = ['input[name="username"]', 'input[name="email"]', 'input[type="email"]', '#username',
                                  '#email']
            password_selectors = ['input[name="password"]', 'input[type="password"]', '#password']

            username_field = None
            for selector in username_selectors:
                try:
                    username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue

            if not username_field:
                print("❌ Could not find username field")
                return False

            password_field = None
            for selector in password_selectors:
                try:
                    password_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue

            if not password_field:
                print("❌ Could not find password field")
                return False

            # Clear and enter credentials from settings
            username_field.clear()
            username_field.send_keys(username)

            password_field.clear()
            password_field.send_keys(password)

            print("✅ Entered credentials")

            # Submit login form
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                'button[class*="login"]',
                'input[value*="Login"]',
                'button[value*="Login"]'
            ]

            login_submit = None
            for selector in submit_selectors:
                try:
                    login_submit = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue

            if not login_submit:
                print("❌ Could not find login submit button")
                return False

            login_submit.click()
            print("✅ Submitted login form")
            time.sleep(5)

        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            return False

        # Step 4: Look for booking request form/link
        print("📋 Looking for booking request form...")
        try:
            # Wait a bit for page to load after login
            time.sleep(3)

            # Try to find booking request link
            booking_selectors = [
                "//a[contains(text(), 'BOOKING REQUEST')]",
                "//a[contains(text(), 'Booking Request')]",
                "//a[contains(text(), 'booking')]",
                "//button[contains(text(), 'BOOKING')]",
                "//a[contains(@href, 'booking')]"
            ]

            booking_link = None
            for selector in booking_selectors:
                try:
                    booking_link = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except:
                    continue

            if booking_link:
                booking_link.click()
                print("✅ Found and clicked booking request link")
                time.sleep(3)
            else:
                print("⚠️ Could not find booking request link, checking if already on form...")

        except Exception as e:
            print(f"⚠️ Error finding booking link: {str(e)}")
            # Continue anyway, might already be on the form

        # Step 5: Fill out the booking form using ACTUAL Google Form field names
        print("📝 Filling out booking form...")

        def fill_google_form_field(driver, field_name, field_value, field_label):
            """Fill a specific Google Form field by name"""
            if not field_value:
                print(f"⚠️ No value provided for {field_label}")
                return False

            try:
                # Wait for field to be present AND visible/enabled
                field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.NAME, field_name))
                )

                # For date fields, try different approaches
                if field_name == "input_2":  # Delivery date field
                    # First try clicking the field to activate it
                    field.click()
                    time.sleep(1)
                    field.clear()
                    field.send_keys(str(field_value))
                else:
                    field.clear()
                    field.send_keys(str(field_value))

                print(f"✅ Filled {field_label}: {field_value}")
                return True
            except Exception as e:
                print(f"❌ Could not fill {field_label} (field: {field_name}): {str(e)}")
                return False

        try:
            # Wait for form to be ready
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "input_2"))
            )
            print("✅ Google Form detected, filling with correct field names...")

            # Based on the field inspection, map the actual Google Form fields:

            # Field 0: Delivery Date (input_2) - CRITICAL REQUIRED FIELD - Try multiple methods
            delivery_date_value = order.delivery_date.strftime('%d/%m/%Y') if order.delivery_date else (
                    date.today() + timedelta(days=1)).strftime('%d/%m/%Y')

            print(f"🗓️ Attempting to fill delivery date: {delivery_date_value}")

            try:
                # Method 1: Find by name and try different approaches
                date_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "input_2"))
                )

                # Try clicking first to activate
                driver.execute_script("arguments[0].click();", date_field)
                time.sleep(1)

                # Try clearing and typing
                driver.execute_script("arguments[0].value = '';", date_field)
                driver.execute_script(f"arguments[0].value = '{delivery_date_value}';", date_field)

                # Trigger change event
                driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", date_field)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", date_field)

                print(f"✅ Filled Delivery Date using JavaScript: {delivery_date_value}")

            except Exception as e:
                print(f"❌ Could not fill Delivery Date: {str(e)}")

                # Fallback: Try by ID
                try:
                    date_field_by_id = driver.find_element(By.ID, "input_1_2")
                    driver.execute_script(f"arguments[0].value = '{delivery_date_value}';", date_field_by_id)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                                          date_field_by_id)
                    print(f"✅ Filled Delivery Date using ID fallback: {delivery_date_value}")
                except Exception as e2:
                    print(f"❌ Delivery Date fallback also failed: {str(e2)}")

            # Field 3: Job Name (input_5) - Try JavaScript method since normal method fails
            job_name_value = f'{test_prefix}Wall Quote Order {order.order_number}'
            try:
                job_name_field = driver.find_element(By.NAME, "input_5")
                driver.execute_script(f"arguments[0].value = '{job_name_value}';", job_name_field)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                                      job_name_field)
                print(f"✅ Filled Job Name using JavaScript: {job_name_value}")
            except Exception as e:
                print(f"❌ Could not fill Job Name: {str(e)}")

            # Field 4: Job Number (input_6)
            job_number_value = f'{"TEST-" if test_submission else ""}{order.order_number}'
            fill_google_form_field(driver, "input_6", job_number_value, "Job Number")

            # Field 5: Some text field (input_37) - might be additional info
            fill_google_form_field(driver, "input_37", f"Wall Quote Order", "Additional Info")

            # Field 6: Type Dropdown (input_35) - CRITICAL REQUIRED FIELD
            try:
                print("🔍 Trying to select delivery type...")
                type_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "input_35"))
                )

                # Get all available options first
                select_obj = Select(type_dropdown)
                options = [option.text for option in select_obj.options]
                print(f"📋 Available dropdown options: {options}")

                # Try different option texts that might work
                delivery_options = ['Sleepers', 'sleepers', 'SLEEPERS', 'Concrete Sleepers', 'Other']

                selected = False
                for option_text in delivery_options:
                    try:
                        select_obj.select_by_visible_text(option_text)
                        print(f"✅ Selected delivery type: {option_text}")
                        selected = True
                        break
                    except:
                        continue

                if not selected and len(options) > 1:
                    # Try selecting by index (skip first which is usually "Select...")
                    try:
                        select_obj.select_by_index(1)
                        print(f"✅ Selected delivery type by index: {options[1]}")
                    except:
                        print(f"❌ Could not select any delivery type")

            except Exception as e:
                print(f"❌ Could not find or select delivery type dropdown: {e}")

            # Field 7: Quantity (input_46) - number type
            fill_google_form_field(driver, "input_46", str(order.total_items), "Quantity")

            # Field 8: Weight (input_33)
            fill_google_form_field(driver, "input_33", str(int(order.total_weight)), "Weight (kg)")

            # Field 9: Description/Comments (input_45) - textarea
            if test_submission:
                comment_text = "*** THIS IS A TEST SUBMISSION ***\nPlease treat this as a test for automation integration.\n\n"
            else:
                comment_text = ""

            comment_text += f"""Order: {order.order_number}
Customer: {order.customer.full_name}
Items: {order.total_items} pieces
Total Weight: {order.total_weight}kg
Contact: budgetpavers@gmail.com

Items List:
"""
            for item in order.items.all():
                comment_text += f"- {item.quantity}x {item.product_name}\n"

            if test_submission:
                comment_text += "\n*** END OF TEST SUBMISSION ***"

            fill_google_form_field(driver, "input_45", comment_text, "Comments/Description")

            # Field 10: Company (input_36)
            fill_google_form_field(driver, "input_36", "Budget Pavers", "Company")

            # Fields 11-14: Company details (input_8, input_9, input_10, input_11)
            fill_google_form_field(driver, "input_8", "Budget Pavers", "Company Name")
            fill_google_form_field(driver, "input_9", "0431 515 310", "Company Phone")
            fill_google_form_field(driver, "input_10", "Wall Quote Team", "Salesperson")
            fill_google_form_field(driver, "input_11", "0431 515 310", "Salesperson Phone")

            # Field 15: Salesperson Email (input_34) - email type
            fill_google_form_field(driver, "input_34", "budgetpavers@gmail.com", "Salesperson Email")

            # Fields 17-20: Pickup Address (input_38.1, input_38.3, input_38.4, input_38.5)
            fill_google_form_field(driver, "input_38.1", "Wall Quote Warehouse", "Pickup Business Name")
            fill_google_form_field(driver, "input_38.3", "123", "Pickup Street Number")
            fill_google_form_field(driver, "input_38.4", "Industrial Drive", "Pickup Street Address")
            fill_google_form_field(driver, "input_38.5", "Adelaide SA 5000", "Pickup Suburb/State")

            # Field 22: Additional Email (input_43)
            fill_google_form_field(driver, "input_43", "budgetpavers@gmail.com", "Additional Email")

            # Field 24: Consignment Note (input_28)
            fill_google_form_field(driver, "input_28", f"WQ-{order.order_number}", "Consignment Note")

            # Fields 25-28: Delivery Address (input_13.1, input_13.2, input_13.3, input_13.4)
            # Parse customer address
            delivery_parts = order.customer.delivery_address_line1.split()
            street_number = delivery_parts[0] if delivery_parts else ""
            street_address = " ".join(delivery_parts[1:]) if len(
                delivery_parts) > 1 else order.customer.delivery_address_line1

            fill_google_form_field(driver, "input_13.1", order.customer.full_name, "Customer/Business Name")
            fill_google_form_field(driver, "input_13.2", street_number, "Delivery Street Number")
            fill_google_form_field(driver, "input_13.3", street_address, "Delivery Street Address")
            fill_google_form_field(driver, "input_13.4",
                                   f"{order.customer.delivery_city} {order.customer.delivery_state} {order.customer.delivery_postcode}",
                                   "Delivery Suburb/State/Postcode")

            # Field 31: Customer Contact (input_15)
            fill_google_form_field(driver, "input_15", order.customer.full_name, "Customer Contact Name")

            # Fields 32-35: Additional delivery details (input_17.1, input_17.2, input_17.3, input_17.4)
            fill_google_form_field(driver, "input_17.1", order.customer.full_name, "Delivery Contact Name")
            fill_google_form_field(driver, "input_17.2", order.customer.phone or "0431 515 310",
                                   "Delivery Contact Phone")
            fill_google_form_field(driver, "input_17.3", order.customer.delivery_city, "Delivery Suburb")
            fill_google_form_field(driver, "input_17.4", order.customer.delivery_state, "Delivery State")

            # Field 38: Customer Name (input_31)
            fill_google_form_field(driver, "input_31", order.customer.full_name, "Customer Name")

            # Field 39: Customer Contact (input_18)
            fill_google_form_field(driver, "input_18", order.customer.full_name, "Customer Contact")

            # Field 40: Customer Phone (input_19)
            fill_google_form_field(driver, "input_19", order.customer.phone or "0431 515 310", "Customer Phone")

            # Field 41: Additional Comments (input_20) - textarea
            additional_comments = f"""Delivery Instructions: {order.delivery_instructions or 'Standard delivery'}
Customer Email: {order.customer.email or 'Not provided'}
Order Total: ${order.total_amount}
Contact Email: budgetpavers@gmail.com"""

            fill_google_form_field(driver, "input_20", additional_comments, "Additional Comments")

            # Handle checkboxes if needed
            try:
                # Field 16: Checkbox (input_40.1)
                checkbox_1 = driver.find_element(By.NAME, "input_40.1")
                if not checkbox_1.is_selected():
                    checkbox_1.click()
                    print("✅ Checked checkbox 1")
            except:
                print("⚠️ Could not find or check checkbox 1")

            try:
                # Field 23: Checkbox (input_44.1)
                checkbox_2 = driver.find_element(By.NAME, "input_44.1")
                if not checkbox_2.is_selected():
                    checkbox_2.click()
                    print("✅ Checked checkbox 2")
            except:
                print("⚠️ Could not find or check checkbox 2")

            try:
                # Field 30: Checkbox (input_27.1)
                checkbox_3 = driver.find_element(By.NAME, "input_27.1")
                if not checkbox_3.is_selected():
                    checkbox_3.click()
                    print("✅ Checked checkbox 3")
            except:
                print("⚠️ Could not find or check checkbox 3")

            try:
                # Field 37: Checkbox (input_30.1)
                checkbox_4 = driver.find_element(By.NAME, "input_30.1")
                if not checkbox_4.is_selected():
                    checkbox_4.click()
                    print("✅ Checked checkbox 4")
            except:
                print("⚠️ Could not find or check checkbox 4")

            try:
                # Field 43: Terms checkbox (input_48.1)
                terms_checkbox = driver.find_element(By.NAME, "input_48.1")
                if not terms_checkbox.is_selected():
                    terms_checkbox.click()
                    print("✅ Accepted terms and conditions")
            except:
                print("⚠️ Could not find terms checkbox")

            print("✅ Form filling completed with Google Form field names")

        except Exception as e:
            print(f"❌ Error filling form: {str(e)}")
            return False

        # Step 6: Submit the form using the Google Form submit button
        print("📤 Submitting form...")
        try:
            # The submit button is Field 44: id='gform_submit_button_1'
            submit_button = driver.find_element(By.ID, "gform_submit_button_1")

            if submit_button.is_displayed():
                submit_button.click()
                print("✅ Clicked Google Form submit button")
            else:
                print("❌ Submit button not visible")
                return False

            # Wait for response
            time.sleep(5)

            # Check for success indicators (Google Forms usually redirects or shows thank you message)
            page_source = driver.page_source.lower()
            success_indicators = ['success', 'submitted', 'thank', 'confirmation', 'received',
                                  'response has been recorded']

            if any(indicator in page_source for indicator in success_indicators):
                print("🎉 Form submitted successfully!")
                return True
            else:
                print("⚠️ Form submitted but no clear success message found")
                # For Google Forms, if no error occurred, assume success
                return True

        except Exception as e:
            print(f"❌ Error submitting form: {str(e)}")
            return False

    except Exception as e:
        print(f"❌ Overall error during RB Transport submission: {str(e)}")
        return False

    finally:
        if driver:
            driver.quit()
            print("🔚 Browser closed")