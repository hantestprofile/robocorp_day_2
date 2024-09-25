from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.Assistant import Assistant


def user_input_task():
    assistant = Assistant()
    assistant.add_heading("Input from user")
    assistant.add_text_input("text_input", placeholder="Please enter URL")
    assistant.add_submit_buttons("Submit", default="Submit")
    result = assistant.run_dialog()
    url = result.text_input
    open_robot_order_website(url)


def open_robot_order_website(url):
    browser.goto(url)   

user_input_task()


@task
def order_robots_from_RobotSpareBin():
    """rcc
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        slowmo=100
    )
    #open_robot_order_website()
    close_annoying_modal()
    fill_the_form(get_orders())
    embed_screenshot_to_receipt()
    archive_receipts()
    

def open_robot_order_website():
    """Navigates to the given URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def get_orders():
    """
    Downloads csv file from the given URL
    Converts csv data to table
    """
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True) 
    library = Tables()
    orders = library.read_table_from_csv("orders.csv", columns=["Order number", "Head", "Body", "Legs", "Address"])
    return orders


def close_annoying_modal():
    """Accepts 'T&Cs' pop-up"""
    page = browser.page()
    page.click("button:text('OK')")


def fill_the_form(orders):
    """For each order(row) in the csv, fill in the details in the web form"""
    page = browser.page()
    for order in orders:
        page.select_option("#head", order["Head"])
        radio_button=page.locator(f".radio input[value='{(order['Body'])}']")
        radio_button.click()
        input_element = page.locator(f"//label[text()='3. Legs:']/following-sibling::input")
        input_element.fill(order["Legs"])
        page.fill("#address", order["Address"])    
        page.click("button:text('Preview')")  
        screenshot_robot(order["Order number"])
        page.click("button:text('ORDER')")
        while page.locator("#order-another").count() == 0: 
            page.click("button:text('ORDER')")
        store_receipt_as_pdf(order["Order number"])
        page.click("button:text('ORDER ANOTHER ROBOT')")
        close_annoying_modal()
            

def store_receipt_as_pdf(order_number):
    """Export each receipt to a separate pdf file"""
    page = browser.page()
    page.wait_for_selector("#receipt") 
    receipts_html = page.locator("#receipt").inner_html()  
    pdf = PDF()
    pdf.html_to_pdf(receipts_html, f"output/receipts/{order_number}.pdf", margin=10)


def screenshot_robot(order_number):        
    """Take a screenshot of the robot image"""
    page = browser.page()
    page.wait_for_selector("#robot-preview-image")
    page.locator("#robot-preview-image").screenshot(path=f"output/screenshots/{order_number}.png")
    

def embed_screenshot_to_receipt():
    """
    Resize all the images (screenshots) to 60% of their original size
    For each receipt and screenshot combination, combine the files into one pdf
    """
    pdf = PDF()
    for num in range(1,21):
        pdf.add_files_to_pdf(files=[f"output/receipts/{num}.pdf", f"output/screenshots/{num}.png:align=center"],target_document=f"output/to_send/Robot-{num}.pdf") 


def archive_receipts():
    """Save all final pdf files stored in the 'to_send' folder as a zip archive folder in the output folder"""
    lib = Archive()
    lib.archive_folder_with_zip('./output/to_send', './output/robots.zip')

     