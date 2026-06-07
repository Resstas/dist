"""
Автотесты для F-Bank

Тесты падают, так как выявляют реальные дефекты:
- Дефект №1: Баланс не обновляется после перевода
- Дефект №2: Нет проверки средств для долларов и евро
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_balance_not_updated_after_transfer_rub(driver, base_url):
    """
    БАГ №1: Баланс не обновляется после перевода
    """
    driver.get(base_url)
    time.sleep(2)
    
    # Кликаем по карточке "Рубли"
    rub_elements = driver.find_elements(By.XPATH, "//h2[contains(text(),'Рубли')]")
    if rub_elements:
        driver.execute_script("arguments[0].click();", rub_elements[0])
    
    time.sleep(1)
    
    # Вводим номер карты
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for inp in inputs:
        if "card" in inp.get_attribute("placeholder") or "0000" in inp.get_attribute("placeholder"):
            inp.send_keys("1234567890123456")
            break
    
    time.sleep(0.5)
    
    # Вводим сумму
    for inp in inputs:
        if inp.get_attribute("type") == "text" and "card" not in inp.get_attribute("placeholder"):
            inp.clear()
            inp.send_keys("500")
            break
    
    # Получаем баланс ДО
    balance_elements = driver.find_elements(By.XPATH, "//span[contains(@id, 'rub') or contains(@id, 'sum')]")
    balance_before = None
    for el in balance_elements:
        text = el.text.replace("'", "").replace(" ", "").replace("₽", "").strip()
        if text.isdigit():
            balance_before = int(text)
            balance_span = el
            break
    
    if balance_before is None:
        balance_before = 30000
    
    # Нажимаем все кнопки на странице (ищем "Перевести")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if "перевести" in btn.text.lower():
            driver.execute_script("arguments[0].click();", btn)
            break
    
    time.sleep(1.5)
    
    # Закрываем алерт
    try:
        alert = driver.switch_to.alert
        alert.accept()
    except:
        pass
    
    time.sleep(1)
    
    # Получаем баланс ПОСЛЕ
    balance_after_text = balance_span.text.replace("'", "").replace(" ", "").replace("₽", "").strip()
    balance_after = int(balance_after_text) if balance_after_text.isdigit() else balance_before
    
    # ПРОВЕРКА: баланс должен уменьшиться
    assert balance_after < balance_before, \
        f"БАГ! Баланс не обновился: было {balance_before}, стало {balance_after}"


def test_transfer_more_than_balance_usd(driver):
    """
    БАГ №2: Нет проверки средств для долларов
    """
    driver.get("http://localhost:8000/?balance=100&reserved=0")
    time.sleep(2)
    
    # Кликаем по карточке "Доллары"
    usd_elements = driver.find_elements(By.XPATH, "//h2[contains(text(),'Доллар')]")
    if usd_elements:
        driver.execute_script("arguments[0].click();", usd_elements[0])
    
    time.sleep(1)
    
    # Вводим номер карты
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for inp in inputs:
        if "card" in inp.get_attribute("placeholder") or "0000" in inp.get_attribute("placeholder"):
            inp.send_keys("1234567890123456")
            break
    
    time.sleep(0.5)
    
    # Вводим сумму 100$
    for inp in inputs:
        if inp.get_attribute("type") == "text" and "card" not in inp.get_attribute("placeholder"):
            inp.clear()
            inp.send_keys("100")
            break
    
    time.sleep(0.5)
    
    # Нажимаем кнопку
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if "перевести" in btn.text.lower():
            driver.execute_script("arguments[0].click();", btn)
            break
    
    time.sleep(1.5)
    
    # Проверяем наличие ошибки
    page_source = driver.page_source.lower()
    has_error = "недостаточно" in page_source
    
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text.lower()
        has_error = has_error or ("недостаточно" in alert_text)
        alert.accept()
    except:
        pass
    
    assert has_error, "БАГ! Нет ошибки при переводе 100$ с балансом 100$"


def test_transfer_more_than_balance_eur(driver):
    """
    БАГ №2: Нет проверки средств для евро
    """
    driver.get("http://localhost:8000/?balance=300&reserved=26")
    time.sleep(2)
    
    # Кликаем по карточке "Евро"
    eur_elements = driver.find_elements(By.XPATH, "//h2[contains(text(),'Евро')]")
    if eur_elements:
        driver.execute_script("arguments[0].click();", eur_elements[0])
    
    time.sleep(1)
    
    # Вводим номер карты
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for inp in inputs:
        if "card" in inp.get_attribute("placeholder") or "0000" in inp.get_attribute("placeholder"):
            inp.send_keys("1234567890123456")
            break
    
    time.sleep(0.5)
    
    # Вводим сумму 300€
    for inp in inputs:
        if inp.get_attribute("type") == "text" and "card" not in inp.get_attribute("placeholder"):
            inp.clear()
            inp.send_keys("300")
            break
    
    time.sleep(0.5)
    
    # Нажимаем кнопку
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if "перевести" in btn.text.lower():
            driver.execute_script("arguments[0].click();", btn)
            break
    
    time.sleep(1.5)
    
    # Проверяем наличие ошибки
    page_source = driver.page_source.lower()
    has_error = "недостаточно" in page_source
    
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text.lower()
        has_error = has_error or ("недостаточно" in alert_text)
        alert.accept()
    except:
        pass
    
    assert has_error, "БАГ! Нет ошибки при переводе 300€ с балансом 300€ и резервом 26€"