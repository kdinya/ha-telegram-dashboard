# 🏠 Telegram Dashboard for Home Assistant

> ⚠️ **BETA**: проєкт у активній розробці. Можливі зміни структури конфігурації та поведінки. Повідомляйте про проблеми в Issues.

[![Home Assistant Add-on](https://img.shields.io/badge/Home%20Assistant-Add--on-blue.svg)](https://www.home-assistant.io/)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/kdinya/ha-telegram-dashboard/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![Add repository to my Home Assistant](https://my.home-assistant.io/badges/repository.svg)](https://my.home-assistant.io/redirect/repository/?repository_url=https%3A%2F%2Fgithub.com%2Fkdinya%2Fha-telegram-dashboard)

> **Візуальний конструктор та менеджер інтерактивних Telegram-дашбордів для Home Assistant без написання сотень рядків YAML-коду.**

---

## ✨ Основні можливості

- 🎨 **Сучасний візуальний конструктор (Ingress UI):** Створюйте та редагуйте розділи меню (`/menu`, `/climate`, `/water`, `/battery`, `/system` тощо) у зручному веб-інтерфейсі прямо в бічній панелі Home Assistant.
- 📱 **Супер-дизайн повідомлень:**
  - Охайні HTML-картки з цитатами (`<blockquote>`).
  - Читабельна деревовидна структура (`├`, `└`).
  - Візуальні графічні прогрес-бари для батарейок (`[▰▰▰▰▰▰▰▰▱▱] 80%`).
  - Інтерактивні інлайн-кнопки з динамічним оновленням стану на кнопці (`[ 🚰 Кран: Відкритий 🟢 ]`).
- 🔐 **Розподіл прав доступу (RBAC):**
  - Визначайте, хто саме має доступ до яких розділів та дій (Адміністратори, Члени родини, Гості).
  - Захист від несанкціонованого керування: блокування критичних дій (перекриття крана, перезавантаження ПК/HA) для сторонніх користувачів.
  - Автоматичне приховування заборонених кнопок.
- 🔄 **Розумне оновлення екранів:** Плавне перемикання розділів через `edit_message` без спаму в чаті та залишення старих повідомлень.
- 🧪 **Покриття тестами:** Повний набір unit-тестів та перевірок GitHub Actions.

---

## 🚀 Встановлення

### Швидкий спосіб (один клік)

Натисніть кнопку — Home Assistant сам додасть репозиторій і відкриє магазин додатків:

[![Open your Home Assistant instance and add the repository](https://my.home-assistant.io/badges/repository.svg)](https://my.home-assistant.io/redirect/repository/?repository_url=https%3A%2F%2Fgithub.com%2Fkdinya%2Fha-telegram-dashboard)

### Вручну

1. У Home Assistant перейдіть у **Налаштування** → **Додатки** → **Магазин додатків**.
2. У правому верхньому кутку натисніть меню (три крапки) → **Репозиторії**.
3. Додайте URL репозиторію:
   ```text
   https://github.com/kdinya/ha-telegram-dashboard
   ```
4. Знайдіть **Telegram Dashboard** у списку та натисніть **Встановити**.
5. У вкладці **Конфігурація** введіть токен бота (отриманий у `@BotFather`).
6. Запустіть аддон та відкрийте **Веб-інтерфейс** на бічній панелі.

---

## 🛠️ Як це працює

```
┌───────────────────────┐         ┌────────────────────────┐         ┌──────────────────────┐
│  Home Assistant Core  │ <=====> │   Telegram Dashboard   │ <=====> │  Telegram Messenger  │
│  (сенсори, вимикачі)  │         │   (Аддон з Ingress UI) │         │  (інтерактивні меню) │
└───────────────────────┘         └────────────────────────┘         └──────────────────────┘
```

1. Аддон автоматично підключається до вашого Home Assistant через внутрішній Supervisor API.
2. Ви відкриваєте Ingress UI в HA, створюєте розділи меню та призначаєте ролі користувачам бота.
3. Бот у Telegram миттєво відповідає на команди та колбеки, формуючи красиві інформативні картки.

---

## 📄 Ліцензія

Розповсюджується за ліцензією [MIT](LICENSE).
Автор: **kdinya** (<kdinya@users.noreply.github.com>).
