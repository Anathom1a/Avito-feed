#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для рандомизации и уникализации текстов описания (Description) объявлений.
Поддерживает:
- Генерацию уникального артикула/хэша (например, SADQGXZTEQS) в конце каждого объявления
- Обновление существующих хэшей в один клик
- Полноценный Spintax рандомизатор шаблона текста с макросами ({city}, {price}, {rand_code})
"""

import sys
import os
import argparse
import re
import random
import string
import xml.etree.ElementTree as ET

def generate_rand_code(length=10, charset='uppercase'):
    if charset == 'alphanumeric':
        chars = string.ascii_uppercase + string.digits
    else:
        chars = string.ascii_uppercase
    return ''.join(random.choices(chars, k=length))

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
    if len(parts) >= 2:
        return parts[1].strip()
    return parts[0].strip()

def update_descriptions(input_xml, output_xml, refresh_codes_only=False, template_file=None, code_len=10):
    tree = ET.parse(input_xml)
    root = tree.getroot()
    ads = root.findall('Ad')
    print(f"[*] Открыт XML-фид: '{input_xml}', найдено {len(ads)} объявлений.")
    
    template = ""
    if template_file and os.path.exists(template_file):
        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read()
        print(f"[+] Загружен шаблон описания из файла: '{template_file}'")
        
    updated = 0
    for ad in ads:
        desc_el = ad.find('Description')
        if desc_el is None:
            desc_el = ET.SubElement(ad, 'Description')
            
        current_desc = desc_el.text or ''
        ad_id = ad.findtext('Id') or ''
        address = ad.findtext('Address') or ''
        city = extract_city(address)
        price = ad.findtext('Price') or ''
        new_code = generate_rand_code(length=code_len)
        
        if refresh_codes_only:
            # Ищем хэш в конце описания (например: KAHYPPJMGB</p> или LVYUMDVSRX</p>)
            # Паттерн ищет последовательность заглавных букв/цифр 8-15 символов перед </p> или в конце текста
            pattern = re.compile(r'([A-Z0-9]{8,15})(\s*</p>|\s*)$')
            if pattern.search(current_desc):
                new_desc = pattern.sub(rf'{new_code}\2', current_desc)
            else:
                # Если хэша нет, добавляем в конец
                if current_desc.endswith('</p>'):
                    new_desc = current_desc[:-4] + f'<br> <br> {new_code}</p>'
                else:
                    new_desc = current_desc + f'\n\n{new_code}'
            desc_el.text = new_desc
            updated += 1
        elif template:
            # Генерация по Spintax шаблону
            spun = spin_text(template)
            spun = spun.replace('{city}', city)
            spun = spun.replace('{город}', city)
            spun = spun.replace('{price}', price)
            spun = spun.replace('{цена}', price)
            spun = spun.replace('{id}', ad_id)
            spun = spun.replace('{rand_code}', new_code)
            spun = spun.replace('{артикул}', new_code)
            
            # Если макрос {rand_code} не был вставлен явно в шаблон, добавляем в конец
            if new_code not in spun:
                if spun.endswith('</p>'):
                    spun = spun[:-4] + f'<br> <br> {new_code}</p>'
                else:
                    spun = spun + f'\n\n{new_code}'
                    
            desc_el.text = spun[:7500] # Лимит Авито 7500 символов
            updated += 1
            
    tree.write(output_xml, encoding='utf-8', xml_declaration=True)
    if refresh_codes_only:
        print(f"[+] Обновлены уникальные коды-артикулы в {updated} объявлениях.")
    else:
        print(f"[+] Тексты описаний сгенерированы по шаблону для {updated} объявлений.")
    print(f"[+] Сохранено в: '{output_xml}'")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Рандомизация текстов и обновление антибан-кодов')
    parser.add_argument('-i', '--input', required=True, help='Входной XML файл')
    parser.add_argument('-o', '--output', default='avito_feed.xml', help='Выходной XML файл')
    parser.add_argument('--refresh-codes', action='store_true', help='Только обновить коды-артикулы (например: SADQGXZTEQS) в конце текстов')
    parser.add_argument('-t', '--template-file', default=None, help='Файл с полным Spintax шаблоном описания')
    parser.add_argument('--code-len', type=int, default=10, help='Длина генерируемого кода (по умолчанию: 10)')
    args = parser.parse_args()
    
    update_descriptions(args.input, args.output, refresh_codes_only=args.refresh_codes, template_file=args.template_file, code_len=args.code_len)
