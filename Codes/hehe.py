import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up Chrome options
options = Options()
options.add_experimental_option("detach", True)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open the website
driver.get("https://civitai.com/search/images?sortBy=images_v6&query=dragon")
driver.maximize_window()

# Set up the directory for saving images
save_directory = "images"
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

# Wait and interact with filters
portrait_label = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Portrait')]"))
)
portrait_label.click()

relevancy_dropdown = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//div[@role='combobox' and @aria-expanded='false']"))
)
relevancy_dropdown.click()

buzz_option = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//div[@role='option' and contains(text(),'Most Reactions')]"))
)
buzz_option.click()
 
time.sleep(3)

for index in range(10):
    try:
        images = driver.find_elements("xpath", "//img[@src]")
        driver.execute_script("arguments[0].click();", images[index])
        high_res_image = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(("xpath", "//img[contains(@class, 'mantine-lrbwmi') and @src]"))
        )
        high_res_url = high_res_image.get_attribute("src")
        if high_res_url:
            img_data = requests.get(high_res_url).content
            image_path = os.path.join(save_directory, f"image_{index + 1}.jpg")
            with open(image_path, 'wb') as file:
                file.write(img_data)
            print(f"Saved {image_path}")

        driver.execute_script("window.history.go(-1)")
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(("xpath", "//img[@src]"))
        )

        time.sleep(2)
    except Exception as e:
        print(f"Failed to download image {index + 1}: {e}")
        driver.execute_script("window.history.go(-1)")
        time.sleep(2)

driver.quit()
