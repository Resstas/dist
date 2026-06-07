"""
Автотесты для F-Bank

Оба теста должны УПАСТЬ, так как выявляют реальные дефекты:
- Дефект №1: Баланс не обновляется после перевода
- Дефект №2: Проверка средств отсутствует для долларов и евро
"""

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
    Ожидание: баланс уменьшается
    Реальность: баланс остаётся прежним → тест падает
    """
    driver.get(base_url)
    
    # 1. Выбираем карточку "Рубли"
    rub_card = driver.find_element(By.XPATH, "//h2[text()='Рубли']/..")
    rub_card.click()
    
    # 2. Вводим номер карты
    card_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='0000 0000 0000 0000']")
    card_input.send_keys("1234567890123456")
    
    # 3. Вводим сумму перевода
    # На странице два поля: номер карты и сумма. Берём второе (индекс 1)
    amount_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
    amount_input = amount_inputs[1]
    amount_input.clear()
    amount_input.send_keys("500")
    
    # 4. Получаем текущий баланс до перевода
    balance_span = driver.find_element(By.ID, "rub-sum")
    balance_before = int(balance_span.text.replace("'", "").replace(" ", ""))
    
    # 5. Нажимаем "Перевести"
    transfer_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Перевести')]")
    transfer_btn.click()
    
    # 6. Закрываем алерт (если появился)
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
    except:
        pass  # если алерта нет — всё равно проверяем баланс
    
    # 7. Получаем баланс после перевода
    balance_after = int(balance_span.text.replace("'", "").replace(" ", ""))
    
    # 8. Ожидание: баланс должен уменьшиться
    # Реальность: баланс не меняется → тест падает
    assert balance_after < balance_before, \
        f"БАГ! Баланс не обновился: было {balance_before}, стало {balance_after}"


# ============================================================
# Тест на ДЕФЕКТ №2: Отсутствие проверки средств для долларов
# ============================================================

def test_transfer_more_than_balance_usd(driver, base_url):
    """
    Баг-репорт №2: Проверка средств отсутствует для долларов
    Ожидание: ошибка "Недостаточно средств"
    Реальность: перевод проходит → тест падает
    """
    driver.get("http://localhost:8000/?balance=100&reserved=0")  # Доллары: 100 $, резерв 0
    
    # 1. Выбираем карточку "Доллары"
    usd_card = driver.find_element(By.XPATH, "//h2[text()='Доллары']/..")
    usd_card.click()
    
    # 2. Вводим номер карты
    card_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='0000 0000 0000 0000']")
    card_input.send_keys("1234567890123456")
    
    # 3. Вводим сумму, которая заведомо превышает доступный остаток
    # Баланс 100 $, комиссия 10% → для суммы 100 $ нужно 110 $ (не хватает)
    amount_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
    amount_input = amount_inputs[1]
    amount_input.clear()
    amount_input.send_keys("100")
    
    # 4. Получаем текущий баланс до перевода
    balance_span = driver.find_element(By.ID, "usd-sum")  # Доллары: usd-sum
    balance_before = int(balance_span.text.replace("'", "").replace(" ", ""))
    
    # 5. Нажимаем "Перевести"
    transfer_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Перевести')]")
    transfer_btn.click()
    
    # 6. Проверяем, появилась ли ошибка "Недостаточно средств"
    # Ищем красное сообщение об ошибке на странице
    error_elements = driver.find_elements(By.XPATH, "//span[contains(text(),'Недостаточно средств')]")
    
    # 7. Если ошибка не появилась — тест падает
    # Реальность: ошибки нет, перевод проходит
    assert len(error_elements) > 0, \
        "БАГ! Нет ошибки 'Недостаточно средств' при переводе с превышением для долларов"
    
    # Дополнительная проверка: баланс не должен измениться
    balance_after = int(balance_span.text.replace("'", "").replace(" ", ""))
    assert balance_after == balance_before, \
        f"БАГ! Баланс изменился: было {balance_before}, стало {balance_after}"