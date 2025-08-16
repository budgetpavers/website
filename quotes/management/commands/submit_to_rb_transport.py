from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from quotes.models import Order
import time
from datetime import datetime


class Command(BaseCommand):
    help = 'Submit order to RB Transport portal automatically'

    def add_arguments(self, parser):
        parser.add_argument('order_id', type=int, help='Order ID to submit to RB Transport')

    def handle(self, *args, **options):
        order_id = options['order_id']

        try:
            order = Order.objects.get(id=order_id)
            self.stdout.write(f'Submitting order {order.order_number} to RB Transport...')

            success = self.submit_to_rb_transport(order)

            if success:
                # Update order status
                order.delivery_status = 'outsourced'
                order.rb_transport_sent = True
                order.rb_transport_sent_at = datetime.now()
                order.save()

                self.stdout.write(
                    self.style.SUCCESS(f'Successfully submitted order {order.order_number} to RB Transport!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to submit order {order.order_number}')
                )

        except Order.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Order with ID {order_id} not found')
            )

    def submit_to_rb_transport(self, order):
        """Submit order to RB Transport portal using Selenium"""

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        driver = None

        try:
            # Initialize Chrome driver
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 10)

            self.stdout.write('Opening RB Transport website...')

            # 1. Go to RB Transport website
            driver.get('https://rbtransport.com.au/')

            # 2. Click login button (assuming it's a button or link)
            try:
                login_button = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'LOGIN')))
                login_button.click()
                self.stdout.write('Clicked login button...')
            except:
                # Try alternative selectors
                try:
                    login_button = driver.find_element(By.XPATH, "//a[contains(text(), 'LOGIN')]")
                    login_button.click()
                except:
                    self.stdout.write('Could not find login button')
                    return False

            # 3. Fill in login credentials
            self.stdout.write('Logging in...')

            # Wait for login form
            username_field = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
            password_field = driver.find_element(By.NAME, 'password')

            # Enter credentials
            username_field.clear()
            username_field.send_keys('Budget Pavers')

            password_field.clear()
            password_field.send_keys('ARBP2906')

            # Submit login form
            login_submit = driver.find_element(By.XPATH, "//input[@type='submit']")
            login_submit.click()

            # 4. Wait for dashboard and navigate to booking
            time.sleep(3)
            self.stdout.write('Logged in successfully, looking for booking form...')

            # Look for booking request link/button
            try:
                booking_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'BOOKING REQUEST')))
                booking_link.click()
                self.stdout.write('Navigated to booking form...')
            except:
                # Try alternative
                try:
                    booking_link = driver.find_element(By.XPATH,
                                                       "//a[contains(text(), 'booking') or contains(text(), 'request')]")
                    booking_link.click()
                except:
                    self.stdout.write('Could not find booking request link')
                    return False

            # 5. Fill out the booking form
            self.stdout.write('Filling out booking form...')

            # Wait for form to load
            time.sleep(2)

            # Fill required fields based on the form image
            try:
                # Delivery Date (required *)
                delivery_date = driver.find_element(By.NAME, 'delivery_date')
                if order.delivery_date:
                    delivery_date.send_keys(order.delivery_date.strftime('%d/%m/%Y'))
                else:
                    # Use tomorrow as default
                    from datetime import date, timedelta
                    tomorrow = date.today() + timedelta(days=1)
                    delivery_date.send_keys(tomorrow.strftime('%d/%m/%Y'))

                # Job name (required *)
                job_name = driver.find_element(By.NAME, 'job_name')
                job_name.send_keys(f'Wall Quote Order {order.order_number}')

                # Job number
                try:
                    job_number = driver.find_element(By.NAME, 'job_number')
                    job_number.send_keys(order.order_number)
                except:
                    pass

                # Type (required *) - dropdown
                try:
                    type_dropdown = Select(driver.find_element(By.NAME, 'type'))
                    type_dropdown.select_by_visible_text('Delivery')  # or appropriate option
                except:
                    pass

                # Quantity (required *)
                quantity = driver.find_element(By.NAME, 'quantity')
                quantity.send_keys(str(order.total_items))

                # Approximate total weight (required *)
                weight = driver.find_element(By.NAME, 'weight')
                weight.send_keys(str(int(order.total_weight)))

                # Company (required *)
                company = driver.find_element(By.NAME, 'company')
                company.send_keys('Budget Pavers')

                # Company Phone (required *)
                company_phone = driver.find_element(By.NAME, 'company_phone')
                company_phone.send_keys('0431 515 310')

                # Salesperson (required *)
                salesperson = driver.find_element(By.NAME, 'salesperson')
                salesperson.send_keys('Wall Quote Team')

                # Salesperson Phone (required *)
                salesperson_phone = driver.find_element(By.NAME, 'salesperson_phone')
                salesperson_phone.send_keys('0431 515 310')

                # Salesperson Email (required *)
                salesperson_email = driver.find_element(By.NAME, 'salesperson_email')
                salesperson_email.send_keys('orders@wallquote.com.au')

                # Pickup Address fields (required *)
                pickup_address = driver.find_element(By.NAME, 'pickup_address')
                pickup_address.send_keys('Wall Quote Warehouse, 123 Industrial Drive, Adelaide SA 5000')

                # Delivery Address fields (required *)
                delivery_address = driver.find_element(By.NAME, 'delivery_address')
                full_address = f"{order.customer.delivery_address_line1}, {order.customer.delivery_city}, {order.customer.delivery_state} {order.customer.delivery_postcode}"
                delivery_address.send_keys(full_address)

                # Customer details
                try:
                    customer_name = driver.find_element(By.NAME, 'customer_name')
                    customer_name.send_keys(order.customer.full_name)

                    customer_phone = driver.find_element(By.NAME, 'customer_phone')
                    customer_phone.send_keys(order.customer.phone or '')
                except:
                    pass

                # Comments/Special Instructions
                try:
                    comments = driver.find_element(By.NAME, 'comments')
                    comment_text = f"""
Order: {order.order_number}
Customer: {order.customer.full_name}
Items: {order.total_items} pieces
Total Weight: {order.total_weight}kg
Delivery Instructions: {order.delivery_instructions or 'Standard delivery'}

Items:
"""
                    for item in order.items.all():
                        comment_text += f"- {item.quantity}x {item.product_name}\n"

                    comments.send_keys(comment_text)
                except:
                    pass

                self.stdout.write('Form filled, submitting...')

                # 6. Submit the form
                submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
                submit_button.click()

                # 7. Wait for confirmation
                time.sleep(3)

                # Check for success message or confirmation
                page_source = driver.page_source.lower()
                if 'success' in page_source or 'submitted' in page_source or 'thank' in page_source:
                    self.stdout.write('Form submitted successfully!')
                    return True
                else:
                    self.stdout.write('Form submission may have failed - no clear success message')
                    return False

            except Exception as e:
                self.stdout.write(f'Error filling form: {str(e)}')
                return False

        except Exception as e:
            self.stdout.write(f'Error during automation: {str(e)}')
            return False

        finally:
            if driver:
                driver.quit()
