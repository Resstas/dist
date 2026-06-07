"""
Автотесты для F-Bank

Оба теста должны УПАСТЬ, так как выявляют реальные дефекты:
- Дефект №1: Баланс не обновляется после перевода (все валюты)
- Дефект №2: Проверка средств отсутствует для Долларов и Евро
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def safe_click(driver, element):
    """Безопасный клик через JS"""
    driver.execute_script("arguments[0].click();", element)


def get_balance(driver, currency_id):
    """Получает баланс по ID элемента"""
    try:
        span = driver.find_element(By.ID, f"{currency_id}-sum")
        text = span.text.replace("'", "").replace(" ", "").replace("₽", "").replace("$", "").replace("€", "").strip()
        return int(text) if text.isdigit() else None
    except:
        return None


# ============================================================
# ДЕФЕКТ №1: Баланс не обновляется после перевода (Рубли)
# ============================================================

def test_balance_not_updated_after_transfer_rub(driver, base_url):
    """
    БАГ: Баланс не обновляется на странице после перевода
    """
    driver.get(base_url)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    time.sleep(1)
    
    # Кликаем по карточке "Рубли"
    rub_card = driver.find_element(By.XPATH, "//h2[text()='Рубли']")
    safe_click(driver, rub_card)
    time.sleep(0.5)
    
    # Вводим номер карты
    card_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='0000 0000 0000 0000']")
    card_input.clear()
    card_input.send_keys("1234567890123456")
    
    # Вводим сумму
    amount_input = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")[1]
    amount_input.clear()
    amount_input.send_keys("500")
    
    # Баланс ДО
    balance_before = get_balance(driver, "rub")
    
    # Нажимаем "Перевести"
    transfer_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Перевести')]")
    safe_click(driver, transfer_btn)
    time.sleep(1)
    
    # Закрываем алерт
    try:
        alert = driver.switch_to.alert
        alert.accept()
    except:
        pass
    
    time.sleep(1)
    
    # Баланс ПОСЛЕ
    balance_after = get_balance(driver, "rub")
    
    # ПРОВЕРКА: баланс должен уменьшиться
    # Реальность: не уменьшается → тест ПАДАЕТ
    assert balance_after is not None and balance_after < balance_before, \
        f"БАГ! Баланс не обновился: было {balance_before}, стало {balance_after}"


# ============================================================
# ДЕФЕКТ №2: Нет проверки средств для ДОЛЛАРОВ
# ============================================================

def test_transfer_more_than_balance_usd(driver):
    """
    БАГ: Проверка средств отсутствует для долларов
    При балансе 100$ и сумме 100$ (комиссия 10$) должно быть НЕДОСТАТОЧНО
    """
    driver.get("http://localhost:8000/?balance=100&reserved=0")
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    time.sleep(1)
    
    # Кликаем по карточке "Доллары"
    usd_card = driver.find_element(By.XPATH, "//h2[text()='Доллары']")
    safe_click(driver, usd_card)
    time.sleep(0.5)
    
    # Вводим номер карты
    card_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='0000 0000 0000 0000']")
    card_input.clear()
    card_input.send_keys("1234567890123456")
    
    # Вводим сумму 100$ (комиссия 10$ → нужно 110$, а есть только 100$)
    amount_input = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")[1]
    amount_input.clear()
    amount_input.send_keys("100")
    
    time.sleep(0.5)
    
    # Нажимаем "Перевести"
    transfer_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Перевести')]")
    safe_click(driver, transfer_btn)
    time.sleep(1)
    
    # Проверяем наличие ошибки на странице или в алерте
    page_text = driver.page_source.lower()
    has_error_on_page = "недостаточно средств" in page_text
    
    has_alert_error = False
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text.lower()
        has_alert_error = "недостаточно" in alert_text
        alert.accept()
    except:
        pass
    
    has_error = has_error_on_page or has_alert_error
    
    # ПРОВЕРКА: должна быть ошибка
    # Реальность: ошибки нет → тест ПАДАЕТ
    assert has_error, \
        "БАГ! Нет ошибки 'Недостаточно средств' при переводе 100$ с балансом 100$ (комиссия 10$)"


# ============================================================
# ДЕФЕКТ №2 (продолжение): Нет проверки средств для ЕВРО
# ============================================================

def test_transfer_more_than_balance_eur(driver):
    """
    БАГ: Проверка средств отсутствует для евро
    При балансе 300€, резерве 26€ и сумме 300€ должно быть НЕДОСТАТОЧНО
    """
    driver.get("http://localhost:8000/?balance=300&reserved=26")
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    time.sleep(1)
    
    # Кликаем по карточке "Евро"
    eur_card = driver.find_element(By.XPATH, "//h2[text()='Евро']")
    safe_click(driver, eur_card)
    time.sleep(0.5)
    
    # Вводим номер карты
    card_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='0000 0000 0000 0000']")
    card_input.clear()
    card_input.send_keys("1234567890123456")
    
    # Вводим сумму 300€ (доступно 274€ из-за резерва 26€)
    amount_input = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")[1]
    amount_input.clear()
    amount_input.send_keys("300")
    
    time.sleep(0.5)
    
    # Нажимаем "Перевести"
    transfer_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Перевести')]")
    safe_click(driver, transfer_btn)
    time.sleep(1)
    
    # Проверяем наличие ошибки
    page_text = driver.page_source.lower()
    has_error_on_page = "недостаточно средств" in page_text
    
    has_alert_error = False
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text.lower()
        has_alert_error = "недостаточно" in alert_text
        alert.accept()
    except:
        pass
    
    has_error = has_error_on_page or has_alert_error
    
    # ПРОВЕРКА: должна быть ошибка
    # Реальность: ошибки нет → тест ПАДАЕТ
    assert has_error, \
        "БАГ! Нет ошибки 'Недостаточно средств' при переводе 300€ с балансом 300€ и резервом 26€"