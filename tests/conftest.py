import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    """Запускает Chrome в headless-режиме для CI"""
    options = Options()
    options.add_argument("--headless")  # без графического интерфейса
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)  # ждать элементы до 5 секунд
    
    yield driver
    
    driver.quit()


@pytest.fixture
def base_url():
    """URL сервиса (замени порт, если нужно)"""
    return "http://localhost:8000/?balance=30000&reserved=20001"