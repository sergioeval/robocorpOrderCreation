from robocorp.tasks import task
from robocorp import browser
import time 
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.FileSystem import FileSystem
from RPA.Archive import Archive

RECEIPTS_PATH = 'output/receipts/'
# for test file with same name always
FINAL_ZIP_FILE = 'output/receipts.zip'

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robot from RobotSpareBin industries inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZiP archive of the receipts and the images.
    """
    # create output pat if not exist 
    create_receipts_path()
    # open website 
    open_robot_order_website()

    # getting orders data 
    orders = get_orders()

    # loop over orders and fill the form
    create_order_from_orders_data(orders=orders)

    # finalmente hacemos zip de todo
    zip_receipts_folder()

    #clean from other files no nneded 
    clean_output_path()


def open_robot_order_website():
    """
    To open the robot order website
    """
    browser.goto(url='https://robotsparebinindustries.com/#/robot-order')
    page = browser.page()

def get_orders():
    """
    TO download the orders and return the results 
    download from https://robotsparebinindustries.com/orders.csv
    """
    http = HTTP()
    http.download(url='https://robotsparebinindustries.com/orders.csv', overwrite=True)
    # read the file 
    csv = Tables()
    data = csv.read_table_from_csv(path='orders.csv')
    return data


def create_order_from_orders_data(orders: Tables):
    for row in orders:
        # process to creat each order 
        close_modal()
        fill_form_from_order_row(row=row)
        

def fill_form_from_order_row(row):
    """
    This fn will take a row and will fill the form with one row 
    """
    page = browser.page()
    print(row)
    page.select_option(selector='#head',index=int(row['Head']))
    # selecting body 
    page.click(selector=f"#id-body-{row['Body']}")
    # fill legs  //*[@id="1720548237558"]
    page.fill(selector="//input[@placeholder='Enter the part number for the legs']", value=row['Legs'])
    # fill address
    page.fill(selector='#address', value=row['Address'])
    # click on preview
    page.click(selector='#preview')
    # click submit but sometimes will failed
    page.click(selector='#order')
    time.sleep(1)
    while not page.is_visible(selector="#order-another"):
        page.click(selector='#order')
        time.sleep(1)
    
    # creating pdf and getting path 
    pdf_path = store_receipt_as_pdf(order_number=row['Order number'])
    image_path =screenshot_robot(order_number=row['Order number'])

    # merge into pdf 
    embed_screenshot_to_receipt(screenshot=image_path, pdf_file=pdf_path)

    # to finish just need to click on order another 
    page.click(selector='#order-another')


def store_receipt_as_pdf(order_number):
    pdf = PDF()
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()

    pdf_path = f'{RECEIPTS_PATH}{order_number}_receipt.pdf'
    pdf.html_to_pdf(receipt_html, pdf_path)
    return pdf_path

def screenshot_robot(order_number):
    page = browser.page()
    image_path = f'{RECEIPTS_PATH}{order_number}_robot.png'
    page.locator('#robot-preview-image').screenshot(path=image_path)
    # page.screenshot(path=image_path, )
    return image_path
    
def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()
    pdf.add_files_to_pdf(files=[screenshot], target_document=pdf_file, append=True)
    # we dont need the png images anymore 
    fs = FileSystem()
    fs.remove_file(path=screenshot, missing_ok=True)


def close_modal():
    page = browser.page()
    if page.is_visible(selector="//div[@class='modal-content']"):
        print('Modal was visible')
        page.click(selector="button:text('OK')")
        return
    print('Modal was not visible')
    return

def create_receipts_path():
    fs = FileSystem()
    fs.create_directory(path=RECEIPTS_PATH, exist_ok=True)

def zip_receipts_folder():
    arc = Archive()
    arc.archive_folder_with_zip(folder=RECEIPTS_PATH, archive_name=FINAL_ZIP_FILE)

def clean_output_path():
    fs = FileSystem()
    fs.remove_directory(path=RECEIPTS_PATH, recursive=True)