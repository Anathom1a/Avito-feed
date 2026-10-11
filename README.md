# 🚀 AviFeed Tool — Профессиональный редактор XML-фида Авито с хостингом на GitHub

Комплексный инструмент (аналог **Avi-tool**) для управления объявлениями, массового обновления фотографий, названий, видеороликов, генерации прайс-листов и защиты от блокировок (антибан) для сервиса **Авито Автозагрузка** (официальный формат XML v3 `Avito.ru`).

---

## 📌 Ключевые возможности

1. **Массовое изменение названий (Title Hub):**
   - Быстрая смена названий во всех 295 объявлениях разом.
   - Поддержка **Spintax**: `{Установка|Инсталляция} {Программ|ПО} {Бессрочно|под ключ}`.
   - Макросы автоподстановки:
     * `{city}` или `{город}` — подставляет город из адреса объявления (например, *Ивантеевка*, *Владивосток*).
     * `{price}` — подставляет цену (например, *180*).
     * `{id}` — уникальный ID объявления.
   - Автоматический контроль лимита длины (до 100 символов по правилам Авито 2026).

2. **Добавление видео (VideoURL Hub):**
   - Прикрепление видеороликов (YouTube, RuTube, VK Видео) ко всем или выбранным объявлениям.
   - Ротация видео: возможность задать список ссылок, которые распределятся между объявлениями.
   - Формирование официального тега `<VideoURL>https://...</VideoURL>`.

3. **Рандомизатор текста и защита от блокировок (Anti-Ban & Spintax):**
   - **Генератор уникальных артикулов/хэшей:** В 1 клик обновляет уникальные последовательности букв (например, `SADQGXZTEQS`, `LVYUMDVSRX`) в конце всех 295 объявлений.
   - **Spintax рандомизатор описаний:** Генерация уникальных текстов для каждого города из мастер-шаблона с макросами `{city}`, `{price}` и `{rand_code}`.

4. **Массовое обновление фото (Photo Manager):**
   - Замена ссылок на фотографии во всех или выбранных объявлениях.
   - **Умная ротация:** случайное перемешивание порядка фото 2–9 при сохранении обложки (Anti-duplicate).
   - Поддержка фото, загруженных прямо в GitHub-репозиторий в папку `images/`.

5. **Конструктор Прайс-Листа (PriceList):**
   - Соответствие официальной XML-структуре Авито: `<PriceList><Service><ServiceName>...<ServicePrice>...`.
   - Табличный редактор с указанием услуги, описания, цены и единицы измерения.
   - Готовые пресеты и применение ко всем объявлениям в один клик.

6. **Хостинг на GitHub Pages:**
   - Постоянный URL для Авито с правильным MIME-типом `application/xml` и Fastly CDN.
   - Публикация обновлений фида прямо из браузера через GitHub API без консоли и Git.

---

## 🛠 Консольные утилиты Python (`tools/`)

Для автоматизации в репозитории подготовлены автономные CLI-скрипты:

### 1. Массовое изменение названий:
```bash
python3 tools/update_titles.py -i avito_feed.xml -o avito_feed.xml -t "{Установка|Настройка} Программ Бессрочно. Компьютерная помощь {city}"
```

### 2. Добавление и управление видео:
```bash
# Добавить одно видео ко всем объявлениям:
python3 tools/update_videos.py -i avito_feed.xml -o avito_feed.xml -u "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Распределить список видеороликов (ротация):
python3 tools/update_videos.py -i avito_feed.xml -o avito_feed.xml -u "url1 | url2 | url3"

# Удалить видео из всех объявлений:
python3 tools/update_videos.py -i avito_feed.xml -o avito_feed.xml --clear
```

### 3. Рандомизация текстов и обновление антибан-кодов:
```bash
# Обновить только уникальные коды (хэши) в конце всех объявлений (например: SADQGXZTEQS):
python3 tools/randomize_text.py -i avito_feed.xml -o avito_feed.xml --refresh-codes

# Сгенерировать описания по Spintax шаблону:
python3 tools/randomize_text.py -i avito_feed.xml -o avito_feed.xml -t template.txt
```

### 4. Массовое обновление фото:
```bash
# Случайная ротация фото 2-9 для уникализации по городам:
python3 tools/update_photos.py -i avito_feed.xml -o avito_feed.xml --shuffle
```

### 5. Обновление прайс-листа:
```bash
python3 tools/update_pricelist.py -i avito_feed.xml -o avito_feed.xml -f default_pricelist.txt
```

### 6. Проверка валидности фида:
```bash
python3 tools/validate_feed.py avito_feed.xml
```

### 7. Конвертация Excel <-> XML:
```bash
# Excel в XML:
python3 tools/excel_to_xml.py -i ads.xlsx -o avito_feed.xml

# XML обратно в Excel:
python3 tools/xml_to_excel.py -i avito_feed.xml -o ads_exported.xlsx
```

---

## 📁 Структура репозитория

```text
avito-feed-manager/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Автодеплой на GitHub Pages и валидация
├── tools/
│   ├── excel_to_xml.py         # Конвертер Excel -> XML
│   ├── xml_to_excel.py         # Конвертер XML -> Excel
│   ├── update_titles.py        # Массовое обновление названий со Spintax
│   ├── update_videos.py        # Массовое добавление и ротация видео
│   ├── randomize_text.py       # Рандомизатор текстов и антибан-кодов
│   ├── update_photos.py        # Ротация и обновление фото
│   ├── update_pricelist.py     # Конструктор прайс-листа
│   └── validate_feed.py        # Валидатор по правилам Авито v3
├── avito_feed.xml              # Готовый XML-фид (295 объявлений)
├── avito_feed_updated.xlsx     # Обновленная таблица Excel
├── default_pricelist.txt       # Шаблон прайс-листа
├── index.html                  # Веб-редактор AviFeed (SPA)
└── README.md                   # Руководство пользователя
```
