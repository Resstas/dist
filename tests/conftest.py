import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    """Запускает Chrome для CI и локально"""
    options = Options()
    options.add_argument("--headless=new")  # более стабильный headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    
    yield driver
    
    driver.quit()


@pytest.fixture
def base_url():
    return "http://localhost:8000/?balance=30000&reserved=20001"