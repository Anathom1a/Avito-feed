#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для массового обновления названий (Title) объявлений.
Поддерживает:
- Spintax: {Установка|Настройка} {программ|ПО}
- Макросы: {city} (город из адреса), {price} (цена), {id}, {manager}
- Контроль длины: автоматически укладывается в лимит Авито (до 100 символов)
"""

import sys
import os
import argparse
import re
import random
import xml.etree.ElementTree as ET

def spin_text(text):
    pattern = re.compile(r'\{([^{}]+)\}')
    while True:
        match = pattern.search(text)
        if not match:
            break
        choices = match.group(1).split('|')
        text = text[:match.start()] + random.choice(choices) + text[match.end():]
    return text

def extract_city(address):
    if not address:
        return ''
    parts = address.split(',')
    # Если указана область и город (например, "Московская обл., Ивантеевка"), берём город
    if len(parts) >= 2:
        return parts[1].strip()
    return parts[0].strip()

def update_titles(input_xml, output_xml, template):
    tree = ET.parse(input_xml)
    root = tree.getroot()
    ads = root.findall('Ad')
    print(f"[*] Открыт XML-фид: '{input_xml}', найдено {len(ads)} объявлений.")
    print(f"[*] Шаблон заголовка: '{template}'")
    
    updated = 0
    for ad in ads:
        title_el = ad.find('Title')
        if title_el is None:
            title_el = ET.SubElement(ad, 'Title')
            
        address = ad.findtext('Address') or ''
        city = extract_city(address)
        price = ad.findtext('Price') or ''
        ad_id = ad.findtext('Id') or ''
        manager = ad.findtext('ManagerName') or ''
        
        # 1. Применяем Spintax
        title_res = spin_text(template)
        
        # 2. Подставляем макросы
        title_res = title_res.replace('{city}', city)
        title_res = title_res.replace('{город}', city)
        title_res = title_res.replace('{price}', price)
        title_res = title_res.replace('{цена}', price)
        title_res = title_res.replace('{id}', ad_id)
        title_res = title_res.replace('{manager}', manager)
        
        # 3. Чистим пробелы и обрезаем до 100 символов (требование Авито)
        title_res = re.sub(r'\s+', ' ', title_res).strip()
        title_el.text = title_res[:100]
        updated += 1
        
    tree.write(output_xml, encoding='utf-8', xml_declaration=True)
    print(f"[+] Успешно обновлены заголовки во всех {updated} объявлениях.")
    print(f"[+] Пример обновленного заголовка: '{ads[0].findtext('Title')}'")
    print(f"[+] Сохранено в: '{output_xml}'")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Массовое обновление названий объявлений с поддержкой Spintax и макросов')
    parser.add_argument('-i', '--input', required=True, help='Входной XML файл')
    parser.add_argument('-o', '--output', default='avito_feed.xml', help='Выходной XML файл')
    parser.add_argument('-t', '--template', required=True, help='Шаблон заголовка (например: "{Установка|Настройка} Программ в г. {city}")')
    args = parser.parse_args()
    
    update_titles(args.input, args.output, args.template)
