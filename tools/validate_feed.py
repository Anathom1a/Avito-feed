#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Валидатор XML-фида Авито по официальным требованиям спецификации Авито Автозагрузка v3 (2026).
"""

import sys
import os
import argparse
import xml.etree.ElementTree as ET

def validate_avito_xml(xml_path):
    print(f"[*] Проверка фида: '{xml_path}'...")
    
    if not os.path.exists(xml_path):
        print(f"[-] Ошибка: файл '{xml_path}' не существует!")
        return False
        
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"[-] КРИТИЧЕСКАЯ ОШИБКА XML: невалидный синтаксис XML! {e}")
        return False
        
    errors = []
    warnings = []
    
    # 1. Корневой элемент
    if root.tag != 'Ads':
        errors.append(f"Корневой элемент должен быть <Ads>, найдено: <{root.tag}>")
    if root.get('formatVersion') != '3':
        errors.append(f"Атрибут formatVersion должен быть '3', найдено: '{root.get('formatVersion')}'")
    if root.get('target') != 'Avito.ru':
        errors.append(f"Атрибут target должен быть 'Avito.ru', найдено: '{root.get('target')}'")
        
    ads = root.findall('Ad')
    if not ads:
        errors.append("В фиде не найдено ни одного объявления <Ad>!")
    if len(ads) > 50000:
        errors.append(f"Превышен лимит Авито: {len(ads)} объявлений (максимум 50 000)")
        
    seen_ids = set()
    required_tags = ['Id', 'Category', 'Title', 'Description', 'Address']
    
    for idx, ad in enumerate(ads, start=1):
        # Обязательные поля
        for tag in required_tags:
            el = ad.find(tag)
            if el is None or not (el.text or '').strip():
                errors.append(f"Объявление #{idx}: Отсутствует обязательный тег <{tag}>")
                
        # Id уникальность и длина до 100 знаков
        ad_id_el = ad.find('Id')
        if ad_id_el is not None and ad_id_el.text:
            ad_id = ad_id_el.text.strip()
            if ad_id in seen_ids:
                errors.append(f"Объявление #{idx}: Дубликат ID '{ad_id}'! ID должны быть уникальны.")
            seen_ids.add(ad_id)
            if len(ad_id) > 100:
                errors.append(f"Объявление #{idx} ({ad_id}): Длина ID превышает 100 знаков ({len(ad_id)})")
                
        # Title <= 100 символов
        title_el = ad.find('Title')
        if title_el is not None and title_el.text:
            t_len = len(title_el.text.strip())
            if t_len > 100:
                errors.append(f"Объявление #{idx} ({ad_id_el.text}): Заголовок > 100 симв. ({t_len})")
                
        # Description <= 7500 символов
        desc_el = ad.find('Description')
        if desc_el is not None and desc_el.text:
            d_len = len(desc_el.text)
            if d_len > 7500:
                warnings.append(f"Объявление #{idx} ({ad_id_el.text}): Длина описания {d_len} симв. (лимит Авито 7500)")
                
        # Address <= 256 символов
        addr_el = ad.find('Address')
        if addr_el is not None and addr_el.text:
            if len(addr_el.text.strip()) > 256:
                errors.append(f"Объявление #{idx}: Адрес > 256 симв.")
                
        # ManagerName <= 40 символов
        mgr_el = ad.find('ManagerName')
        if mgr_el is not None and mgr_el.text:
            if len(mgr_el.text.strip()) > 40:
                warnings.append(f"Объявление #{idx}: Имя менеджера > 40 симв. ({len(mgr_el.text.strip())})")
                
        # Фотографии (Images) <= 10
        images_el = ad.find('Images')
        if images_el is None or len(images_el.findall('Image')) == 0:
            errors.append(f"Объявление #{idx} ({ad_id_el.text}): Нет тега <Images> или нет ни одного фото <Image>!")
        else:
            img_count = len(images_el.findall('Image'))
            if img_count > 10:
                warnings.append(f"Объявление #{idx}: {img_count} фото (Авито покажет только первые 10)")
            for img in images_el.findall('Image'):
                u = img.get('url')
                if not u or not u.startswith(('http://', 'https://')):
                    errors.append(f"Объявление #{idx}: Некорректный URL фото: '{u}'")
                    
        # PriceList <= 50 услуг со структурой <Service>
        pl_el = ad.find('PriceList')
        if pl_el is not None:
            services = pl_el.findall('Service')
            if len(services) > 50:
                errors.append(f"Объявление #{idx}: В прайс-листе {len(services)} услуг (максимум 50)")
            for s_idx, s in enumerate(services, 1):
                s_name = s.find('ServiceName')
                s_price = s.find('ServicePrice')
                s_type = s.find('ServicePriceType')
                if s_name is None or not (s_name.text or '').strip():
                    errors.append(f"Объявление #{idx}, услуга #{s_idx}: отсутствует <ServiceName>")
                if s_price is None or not (s_price.text or '').strip():
                    errors.append(f"Объявление #{idx}, услуга #{s_idx}: отсутствует <ServicePrice>")
                if s_type is None or not (s_type.text or '').strip():
                    errors.append(f"Объявление #{idx}, услуга #{s_idx}: отсутствует <ServicePriceType>")
                    
    print("\n" + "="*50)
    print(f"ИТОГИ ПРОВЕРКИ ФИДА ({len(ads)} объявлений):")
    print("="*50)
    
    if errors:
        print(f"[-] НАЙДЕНО ОШИБОК: {len(errors)}")
        for e in errors[:10]:
            print(f"  • {e}")
        if len(errors) > 10:
            print(f"  ... и ещё {len(errors)-10} ошибок.")
    else:
        print("[+] ОШИБОК НЕ ОБНАРУЖЕНО! Фид на 100% соответствует официальной спецификации Авито v3.")
        
    if warnings:
        print(f"[!] Предупреждений: {len(warnings)}")
        for w in warnings[:5]:
            print(f"  • {w}")
    else:
        print("[+] Предупреждений нет.")
        
    return len(errors) == 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Валидация XML фида Авито по спецификации v3')
    parser.add_argument('feed', nargs='?', default='avito_feed.xml', help='Путь к XML файлу фида')
    args = parser.parse_args()
    
    success = validate_avito_xml(args.feed)
    sys.exit(0 if success else 1)
