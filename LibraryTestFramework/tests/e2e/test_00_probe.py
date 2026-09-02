"""TEMPORARY input-delivery diagnostic probe (runs first, writes input_probe.json).

Investigates why Chrome drops trusted Selenium input (keystrokes/clicks) on
the home catalogue: captures driver versions, reduced-motion state, animation
activity, DOM event traces for send_keys and element.click(), hit-testing at
the interaction points, and whether the debounced search fetch fires from the
browser side. Results go to tests/e2e/screenshots/input_probe.json, which the
CI artifact upload already picks up. Remove once the issue is resolved.
"""
import json
import os
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytestmark = pytest.mark.e2e

INSTRUMENT = """
window.__evts = [];
['pointerdown','mousedown','mouseup','click','keydown','beforeinput','input','focus'].forEach(t => {
  document.addEventListener(t, e => {
    const tgt = e.target;
    window.__evts.push({t: t, tgt: tgt.tagName + (tgt.getAttribute && tgt.getAttribute('data-testid') ? '#' + tgt.getAttribute('data-testid') : ''), trusted: e.isTrusted});
  }, true);
});
return 'ok';
"""


def _make_driver():
    options = Options()
    chrome_binary = os.getenv("CHROME_BINARY")
    if chrome_binary and os.path.isfile(chrome_binary):
        options.binary_location = chrome_binary
    options.add_argument("--headless=new")
    options.add_argument("--force-prefers-reduced-motion")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-gpu")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
    driver_path = os.getenv("CHROMEDRIVER_PATH")
    service = ChromeService(executable_path=driver_path) if driver_path else None
    return webdriver.Chrome(service=service, options=options) if service else webdriver.Chrome(options=options)


def _api_book_requests(driver):
    calls = {}
    for entry in driver.get_log("performance"):
        try:
            msg = json.loads(entry["message"])["message"]
        except Exception:
            continue
        if msg.get("method") == "Network.responseReceived":
            resp = msg["params"]["response"]
            if ":8000" in resp["url"] and "/books" in resp["url"]:
                calls[resp["url"]] = resp["status"]
    return calls


def test_input_delivery_probe():
    driver = _make_driver()
    driver.implicitly_wait(0)
    results = {}
    try:
        caps = driver.capabilities
        chrome_info = caps.get("chrome") or {}
        results["browserVersion"] = caps.get("browserVersion")
        results["chromedriverVersion"] = chrome_info.get("chromedriverVersion", "?")[:80]
        results["headless_flag"] = chrome_info.get("headless", "?")

        driver.get("http://localhost:3000")
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="login-username"]'))
        )
        driver.find_element(By.CSS_SELECTOR, '[data-testid="login-username"]').send_keys("member1")
        driver.find_element(By.CSS_SELECTOR, '[data-testid="login-password"]').send_keys("Member123!")
        driver.find_element(By.CSS_SELECTOR, '[data-testid="login-submit"]').click()
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="nav-home"]'))
        )
        WebDriverWait(driver, 40).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid^="book-card-"]'))
        )
        time.sleep(2)
        results["login_typing"] = "OK"

        results["matchMedia_reduced_motion"] = driver.execute_script(
            "return matchMedia('(prefers-reduced-motion: reduce)').matches"
        )
        results["search_input_count"] = driver.execute_script(
            "return document.querySelectorAll('[data-testid=\"search-input\"]').length"
        )
        results["viewport"] = driver.execute_script(
            "return JSON.stringify({w: innerWidth, h: innerHeight, dpr: devicePixelRatio, hasFocus: document.hasFocus()})"
        )
        results["orb_animation"] = driver.execute_script(
            """
            const orb = document.querySelector('[data-testid="home-hero"] div[aria-hidden]');
            if (!orb) return 'NO ORB';
            const t1 = getComputedStyle(orb).transform;
            return new Promise(res => setTimeout(() => {
              const t2 = getComputedStyle(orb).transform;
              res(JSON.stringify({animating: t1 !== t2, t1: t1.slice(0, 40), t2: t2.slice(0, 40)}));
            }, 600));
            """
        )
        results["input_geometry"] = driver.execute_script(
            """
            const i = document.querySelector('[data-testid="search-input"]');
            const r = i.getBoundingClientRect();
            const top = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
            return JSON.stringify({top: Math.round(r.top), bottom: Math.round(r.bottom), innerH: innerHeight,
                                   hitTarget: top ? top.tagName + '#' + (top.getAttribute('data-testid') || '') : 'null'});
            """
        )

        # --- send_keys on the search input with event capture ---
        driver.execute_script(INSTRUMENT)
        inp = driver.find_element(By.CSS_SELECTOR, '[data-testid="search-input"]')
        inp.clear()
        inp.send_keys("Clean")
        time.sleep(4)
        results["typing"] = {
            "events": driver.execute_script("return JSON.stringify(window.__evts.slice(0, 12))"),
            "value_after": inp.get_attribute("value"),
            "card_count": len(driver.find_elements(By.CSS_SELECTOR, '[data-testid^="book-card-"]')),
            "books_count_text": (lambda els: els[0].text if els else "MISSING")(
                driver.find_elements(By.CSS_SELECTOR, '[data-testid="books-count"]')
            ),
            "books_api_calls": _api_book_requests(driver),
        }

        # --- native click on the first card with event capture ---
        driver.execute_script("window.__evts = []")
        driver.execute_script(
            "document.querySelector('[data-testid=\"book-card-1\"]').scrollIntoView({block:'center'});"
        )
        time.sleep(0.8)
        card = driver.find_element(By.CSS_SELECTOR, '[data-testid="book-card-1"]')
        card.click()
        time.sleep(2)
        results["card_click"] = {
            "events": driver.execute_script("return JSON.stringify(window.__evts.slice(0, 10))"),
            "detail_present": bool(
                driver.find_elements(By.CSS_SELECTOR, '[data-testid="book-detail-page"]')
            ),
        }
        results["console_severe"] = [
            e["message"][:150]
            for e in driver.get_log("browser")
            if e["level"] == "SEVERE"
        ]
    except Exception as exc:
        results["probe_error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    finally:
        out = os.path.join(os.path.dirname(__file__), "screenshots", "input_probe.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1)
        print("INPUT PROBE RESULTS:\n" + json.dumps(results, indent=1))
        driver.quit()
    assert "probe_error" not in results
