"""
Автотесты для F-Bank

Оба теста должны УПАСТЬ, так как выявляют реальные дефекты:
- Дефект №1: Баланс не обновляется после перевода
- Дефект №2: Проверка средств отсутствует для долларов и евро
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ============================================================
# Тест на ДЕФЕКТ №1: Баланс не обновляется после перевода
# ============================================================

def test_balance_not_updated_after_transfer_rub(driver, base_url):
    """
    Баг-репорт №1: Баланс на странице не обновляется после перевода
    """
    driver.get(base_url)
    
    # Ждём загрузки страницы (появление заголовка)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    
    time.sleep(1)  # даём React время на рендер
    
    # 1. Кликаем по карточке "Рубли"
    rub_cards = driver.find_elements(By.XPATH, "//h2[text()='Рубли']")
    if rub_cards:
        rub_cards[0].click()
    else:
        # Альтернативный вариант
        driver.find_element(By.XPATH, "//h2[contains(text(),'Рубли')]").click()
    
    time.sleep(0.5)
    
    # 2. Вводим номер карты
    card_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
    card_input = None
    for inp in card_inputs:
        if "0000" in inp.get_attribute("placeholder") or inp.get_attribute("placeholder") == "":
            card_input = inp
            break
    
    if card_input:
        card_input.clear()
        card_input.send_keys("1234567890123456")
    
    time.sleep(0.5)
    
    # 3. Вводим сумму
    amount_input = None
    for inp in card_inputs:
        if inp != card_input:
            amount_input = inp
            break
    
    if amount_input:
        amount_input.clear()
        amount_input.send_keys("500")
    
    time.sleep(0.5)
    
    # 4. Получаем баланс ДО
    balance_spans = driver.find_elements(By.CSS_SELECTOR, "span[id$='-sum']")
    balance_before = None
    for span in balance_spans:
        text = span.text.replace("'", "").replace(" ", "").replace("₽", "").replace("$", "").replace("€", "").strip()
        if text.isdigit():
            balance_before = int(text)
            balance_span = span
            break
    
    if balance_before is None:
        balance_before = 30000  # fallback
    
    # 5. Нажимаем кнопку "Перевести"
    buttons = driver.find_elements(By.TAG_NAME, "button")
    transfer_btn = None
    for btn in buttons:
        if "Перевести" in btn.text or "перевести" in btn.text.lower():
            transfer_btn = btn
            break
    
    if transfer_btn:
        driver.execute_script("arguments[0].click();", transfer_btn)
    
    time.sleep(1)
    
    # 6. Закрываем алерт
    try:
        alert = driver.switch_to.alert
        alert.accept()
    except:
        pass
    
    time.sleep(1)
    
    # 7. Получаем баланс ПОСЛЕ
    balance_after_text = balance_span.text.replace("'", "").replace(" ", "").replace("₽", "").strip()
    balance_after = int(balance_after_text) if balance_after_text.isdigit() else balance_before
    
    # 8. ПРОВЕРКА: баланс должен уменьшиться
    # Если баланс не изменился — тест падает (это и есть БАГ)
    assert balance_after < balance_before, \
        f"БАГ! Баланс не обновился после перевода: было {balance_before}, стало {balance_after}"


# ============================================================
# Тест на ДЕФЕКТ №2: Отсутствие проверки средств для долларов
# ============================================================

def test_transfer_more_than_balance_usd(driver):
    """
    Баг-репорт №2: Нет проверки средств для долларов
    """
    driver.get("http://localhost:8000/?balance=100&reserved=0")
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    
    time.sleep(1)
    
    # 1. Кликаем по карточке "Доллары"
    usd_cards = driver.find_elements(By.XPATH, "//h2[text()='Доллары']")
    if usd_cards:
        usd_cards[0].click()
    else:
        driver.find_element(By.XPATH, "//h2[contains(text(),'Доллар')]").click()
    
    time.sleep(0.5)
    
    # 2. Вводим номер карты
    card_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
    card_input = None
    for inp in card_inputs:
        if "0000" in inp.get_attribute("placeholder") or inp.get_attribute("placeholder") == "":
            card_input = inp
            break
    
    if card_input:
        card_input.clear()
        card_input.send_keys("1234567890123456")
    
    time.sleep(0.5)
    
    # 3. Вводим сумму 100 $ (при балансе 100 $ и комиссии 10% не хватает)
    amount_input = None
    for inp in card_inputs:
        if inp != card_input:
            amount_input = inp
            break
    
    if amount_input:
        amount_input.clear()
        amount_input.send_keys("100")
    
    time.sleep(0.5)
    
    # 4. Нажимаем кнопку "Перевести"
    buttons = driver.find_elements(By.TAG_NAME, "button")
    transfer_btn = None
    for btn in buttons:
        if "Перевести" in btn.text or "перевести" in btn.text.lower():
            transfer_btn = btn
            break
    
    if transfer_btn:
        driver.execute_script("arguments[0].click();", transfer_btn)
    
    time.sleep(1)
    
    # 5. Проверяем наличие ошибки
    page_text = driver.page_source.lower()
    has_error = "недостаточно средств" in page_text
    
    # Проверяем алерт
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text.lower()
        has_error = has_error or ("недостаточно" in alert_text)
        alert.accept()
    except:
        pass
    
    # 6. ПРОВЕРКА: должна быть ошибка
    # Если ошибки нет — тест падает (это и есть БАГ)
    assert has_error, \
        "БАГ! Нет ошибки 'Недостаточно средств' при переводе 100$ с балансом 100$ (комиссия 10$)"