#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для массового добавления и редактирования прайс-листа в XML-фиде Авито.
Генерирует официальную структуру <PriceList><Service>...
"""

import sys
import os
import argparse
import xml.etree.ElementTree as ET

DEFAULT_SERVICES = [
    "Установка операционной системы Windows / macOS||1000|Да|за услугу",
    "Установка офисных программ (MS Office, Word, Excel)||500|Да|за услугу",
    "Установка графических программ (Photoshop, CorelDRAW)||700|Да|за услугу",
    "Установка программ видеомонтажа (Premiere, DaVinci)||800|Да|за услугу",
    "Установка САПР и 3D-программ (AutoCAD, 3ds Max, Archicad)||1200|Да|за услугу",
    "Настройка программ для мебели и ЧПУ (Базис, Artcam, NC-Studio)||1500|Да|за услугу",
    "Настройка ЭЦП, КриптоПро и сертификатов для торгов и ФНС||1000|Да|за услугу",
    "Удаленная компьютерная помощь и диагностика||500|Да|за услугу"
]

def parse_lines_to_services(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    services = []
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        while len(parts) < 5: parts.append('')
        s_name, s_title, s_price, s_from, s_type = parts[0], parts[1], parts[2], parts[3], parts[4] or 'за услугу'
        if not s_name and s_title: s_name = 'Своя услуга'
        if s_name:
            services.append({
                'ServiceName': s_name,
                'ServiceTitle': s_title,
                'ServicePrice': s_price,
                'ServiceStartingPrice': s_from,
                'ServicePriceType': s_type
            })
    return services[:50]

def update_pricelist_in_xml(input_xml, output_xml, pricelist_text=None, pricelist_file=None, replace_existing=True):
    tree = ET.parse(input_xml)
    root = tree.getroot()
    ads = root.findall('Ad')
    print(f"[*] Открыт XML-фид: '{input_xml}', найдено {len(ads)} объявлений.")
    
    raw_text = ""
    if pricelist_file and os.path.exists(pricelist_file):
        with open(pricelist_file, 'r', encoding='utf-8') as f:
            raw_text = f.read().strip()
    elif pricelist_text:
        raw_text = pricelist_text.strip()
    else:
        raw_text = '\n'.join(DEFAULT_SERVICES)
        
    services = parse_lines_to_services(raw_text)
    
    updated = 0
    for ad in ads:
        pl_elem = ad.find('PriceList')
        if pl_elem is None:
            pl_elem = ET.SubElement(ad, 'PriceList')
            
        existing_services = pl_elem.findall('Service')
        if not existing_services or replace_existing:
            pl_elem.clear()
            for s in services:
                s_elem = ET.SubElement(pl_elem, 'Service')
                ET.SubElement(s_elem, 'ServiceName').text = s['ServiceName']
                if s['ServiceTitle']:
                    ET.SubElement(s_elem, 'ServiceTitle').text = s['ServiceTitle']
                if s['ServicePrice']:
                    ET.SubElement(s_elem, 'ServicePrice').text = s['ServicePrice']
                if s['ServiceStartingPrice'] in ['Да', 'true', 'True', '1']:
                    ET.SubElement(s_elem, 'ServiceStartingPrice').text = 'Да'
                ET.SubElement(s_elem, 'ServicePriceType').text = s['ServicePriceType']
            updated += 1
            
    tree.write(output_xml, encoding='utf-8', xml_declaration=True)
    print(f"[+] Прайс-лист ({len(services)} услуг) обновлен в {updated} объявлениях.")
    print(f"[+] Сохранено в: '{output_xml}'")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Массовое обновление прайс-листа в фиде Авито')
    parser.add_argument('--input', '-i', required=True, help='Входной XML файл фида')
    parser.add_argument('--output', '-o', default='avito_feed.xml', help='Выходной XML файл')
    parser.add_argument('--text', '-t', default=None, help='Строка прайс-листа (строки через \\n)')
    parser.add_argument('--file', '-f', default=None, help='Файл с прайс-листом')
    parser.add_argument('--only-empty', action='store_true', help='Обновлять только объявления без прайса')
    args = parser.parse_args()
    update_pricelist_in_xml(args.input, args.output, pricelist_text=args.text, pricelist_file=args.file, replace_existing=not args.only_empty)
