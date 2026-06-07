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


def wait_and_find_element(driver, by, selector, timeout=10):
    """Ожидает появления элемента и возвращает его"""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )


# ============================================================
# Тест на ДЕФЕКТ №1: Баланс не обновляется после перевода
# ============================================================

def test_balance_not_updated_after_transfer_rub(driver, base_url):
    """
    Баг-репорт №1: Баланс на странице не обновляется после перевода
    Ожидание: баланс уменьшается
    Реальность: баланс остаётся прежним → тест падает
    """
    driver.get(base_url)
    
    # Ожидаем загрузки страницы
    wait_and_find_element(driver, By.TAG_NAME, "h1")
    
    # 1. Выбираем карточку "Рубли"
    rub_card = driver.find_element(By.XPATH, "//h2[text()='Рубли']/..")
    driver.execute_script("arguments[0].click();", rub_card)  # клик через JS надёжнее
    
    time.sleep(0.5)  # небольшая пауза для React
    
    # 2. Вводим номер карты
    card_input = wait_and_find_element(driver, By.CSS_SELECTOR, "input[placeholder='0000 0000 0000 0000']")
    card_input.clear()
    card_input.send_keys("1234567890123456")
    
    # 3. Вводим сумму перевода
    amount_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
    # Фильтруем: нам нужен input для суммы (не для карты)
    amount_input = None
    for inp in amount_inputs:
        if inp.get_attribute("placeholder") != "0000 0000 0000 0000":
            amount_input = inp
            break
    
    if amount_input is None:
        amount_input = amount_inputs[1]  # fallback
    
    amount_input.clear()
    amount_input.send_keys("500")
    
    # 4. Получаем текущий баланс до перевода
    balance_span = wait_and_find_element(driver, By.ID, "rub-sum")
    balance_text = balance_span.text.replace("'", "").replace(" ", "").replace("₽", "").strip()
    balance_before = int(balance_text) if balance_text.isdigit() else 0
    
    # 5. Находим и нажимаем кнопку "Перевести"
    # Пробуем несколько вариантов локаторов
    transfer_btn = None
    try:
        transfer_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Перевести')]")
    except:
        try:
            transfer_btn = driver.find_element(By.XPATH, "//button[contains(.,'Перевести')]")
        except:
            transfer_btn = driver.find_element(By.CSS_SELECTOR, "button[type='button']")
    
    driver.execute_script("arguments[0].click();", transfer_btn)
    
    # 6. Закрываем алерт (если появился)
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
    except:
        pass
    
    time.sleep(1)  # даём время на возможное обновление
    
    # 7. Получаем баланс после перевода
    balance_after_text = balance_span.text.replace("'", "").replace(" ", "").replace("₽", "").strip()
    balance_after = int(balance_after_text) if balance_after_text.isdigit() else 0
    
    # 8. Ожидание: баланс должен уменьшиться
    # Реальность: баланс не меняется → тест падает
    assert balance_after < balance_before, \
        f"БАГ! Баланс не обновился: было {balance_before}, стало {balance_after}"


# ============================================================
# Тест на ДЕФЕКТ №2: Отсутствие проверки средств для долларов
# ============================================================

def test_transfer_more_than_balance_usd(driver):
    """
    Баг-репорт №2: Проверка средств отсутствует для долларов
    Ожидание: ошибка "Недостаточно средств"
    Реальность: перевод проходит → тест падает
    """
    driver.get("http://localhost:8000/?balance=100&reserved=0")
    
    # Ожидаем загрузки
    wait_and_find_element(driver, By.TAG_NAME, "h1")
    
    # 1. Выбираем карточку "Доллары"
    usd_card = driver.find_element(By.XPATH, "//h2[text()='Доллары']/..")
    driver.execute_script("arguments[0].click();", usd_card)
    
    time.sleep(0.5)
    
    # 2. Вводим номер карты
    card_input = wait_and_find_element(driver, By.CSS_SELECTOR, "input[placeholder='0000 0000 0000 0000']")
    card_input.clear()
    card_input.send_keys("1234567890123456")
    
    # 3. Вводим сумму 100 $ (при балансе 100 $ и комиссии 10 % должно быть недостаточно)
    amount_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
    amount_input = None
    for inp in amount_inputs:
        if inp.get_attribute("placeholder") != "0000 0000 0000 0000":
            amount_input = inp
            break
    
    if amount_input is None:
        amount_input = amount_inputs[1]
    
    amount_input.clear()
    amount_input.send_keys("100")
    
    time.sleep(0.5)
    
    # 4. Нажимаем "Перевести"
    try:
        transfer_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Перевести')]")
    except:
        transfer_btn = driver.find_element(By.CSS_SELECTOR, "button[type='button']")
    
    driver.execute_script("arguments[0].click();", transfer_btn)
    
    time.sleep(1)
    
    # 5. Проверяем, появилась ли ошибка
    # Сначала пробуем найти текст ошибки на странице
    page_source = driver.page_source
    has_error = "Недостаточно средств" in page_source
    
    # Если алерт — проверяем его
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        has_error = has_error or ("недостаточно" in alert_text.lower())
    except:
        pass
    
    # 6. Ожидание: должна быть ошибка
    # Реальность: ошибки нет → тест падает
    assert has_error, \
        "БАГ! Нет ошибки 'Недостаточно средств' при переводе с превышением для долларов"