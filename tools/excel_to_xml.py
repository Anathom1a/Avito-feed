#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конвертер объявлений Авито из Excel (.xlsx) в XML-фид (формат v3 Avito.ru).
Поддерживает CDATA для описания и прайс-листа, соответствие спецификации Авито.
"""

import sys
import os
import argparse
import openpyxl

def clean_val(val):
    if val is None:
        return ''
    s = str(val).strip()
    return '' if s == 'None' else s

def load_ads_from_excel(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    target_sheet = None
    for name in wb.sheetnames:
        if name != 'Инструкция' and not name.startswith('Спр-'):
            target_sheet = wb[name]
            break
    if not target_sheet:
        target_sheet = wb.active
        
    print(f"[+] Чтение листа: '{target_sheet.title}' ({target_sheet.max_row} строк)")
    
    headers = []
    for c in range(1, target_sheet.max_column + 1):
        headers.append(clean_val(target_sheet.cell(2, c).value))
        
    ads = []
    for r in range(5, target_sheet.max_row + 1):
        ad = {}
        for c, h in enumerate(headers):
            if not h:
                continue
            ad[h] = target_sheet.cell(r, c + 1).value
            
        ad_id = clean_val(ad.get('Id'))
        if not ad_id:
            continue
        ads.append(ad)
        
    print(f"[+] Загружено объявлений: {len(ads)}")
    return ads

def escape_xml(s):
    if not s:
        return ''
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

def build_ad_xml(item, default_price_list=None, new_photos=None, shuffle_photos=False):
    lines = ['\t<Ad>']
    
    cat = clean_val(item.get('Category')) or 'Предложение услуг'
    lines.append(f'\t\t<Category>{escape_xml(cat)}</Category>')
    
    price = clean_val(item.get('Price'))
    if price:
        lines.append(f'\t\t<Price>{escape_xml(price)}</Price>')
        
    img_urls_raw = new_photos if new_photos else clean_val(item.get('ImageUrls'))
    urls = [u.strip() for u in img_urls_raw.split('|') if u.strip()]
    if shuffle_photos and len(urls) > 1:
        import random
        first = urls[0]
        rest = urls[1:]
        random.shuffle(rest)
        urls = [first] + rest
        
    if urls:
        lines.append('\t\t<Images>')
        for u in urls[:10]:
            lines.append(f'\t\t\t<Image url="{escape_xml(u)}"/>')
        lines.append('\t\t</Images>')
        
    cm = clean_val(item.get('ContactMethod')) or 'По телефону и в сообщениях'
    lines.append(f'\t\t<ContactMethod>{escape_xml(cm)}</ContactMethod>')
    
    for promo_field in ['Promo', 'PromoAutoOptions', 'PromoManualOptions']:
        val = clean_val(item.get(promo_field))
        if val:
            lines.append(f'\t\t<{promo_field}>{escape_xml(val)}</{promo_field}>')
            
    ad_id = clean_val(item.get('Id'))
    lines.append(f'\t\t<Id>{escape_xml(ad_id)}</Id>')
    
    db = clean_val(item.get('DateBegin'))
    if db:
        lines.append(f'\t\t<DateBegin>{escape_xml(db)}</DateBegin>')
        
    de = clean_val(item.get('DateEnd') or item.get('AvitoDateEnd'))
    if de:
        lines.append(f'\t\t<DateEnd>{escape_xml(de)}</DateEnd>')
        
    fee = clean_val(item.get('ListingFee')) or 'Package'
    lines.append(f'\t\t<ListingFee>{escape_xml(fee)}</ListingFee>')
    
    status = clean_val(item.get('AdStatus'))
    if status:
        lines.append(f'\t\t<AdStatus>{escape_xml(status)}</AdStatus>')
        
    avito_id = clean_val(item.get('AvitoId'))
    if avito_id:
        lines.append(f'\t\t<AvitoId>{escape_xml(avito_id)}</AvitoId>')
        
    manager = clean_val(item.get('ManagerName'))
    if manager:
        lines.append(f'\t\t<ManagerName>{escape_xml(manager)}</ManagerName>')
        
    phone = clean_val(item.get('ContactPhone'))
    if phone:
        lines.append(f'\t\t<ContactPhone>{escape_xml(phone)}</ContactPhone>')
        
    title = clean_val(item.get('Title'))
    lines.append(f'\t\t<Title>{escape_xml(title)}</Title>')
    
    desc = clean_val(item.get('Description'))
    if desc:
        lines.append(f'\t\t<Description><![CDATA[{desc}]]></Description>')
    else:
        lines.append('\t\t<Description></Description>')
        
    address = clean_val(item.get('Address'))
    if address:
        lines.append(f'\t\t<Address>{escape_xml(address)}</Address>')
        
    lat = clean_val(item.get('Latitude'))
    if lat:
        lines.append(f'\t\t<Latitude>{escape_xml(lat)}</Latitude>')
    lon = clean_val(item.get('Longitude'))
    if lon:
        lines.append(f'\t\t<Longitude>{escape_xml(lon)}</Longitude>')
        
    ic = clean_val(item.get('InternetCalls'))
    if ic:
        lines.append(f'\t\t<InternetCalls>{escape_xml(ic)}</InternetCalls>')
    cd = clean_val(item.get('CallsDevices'))
    if cd:
        lines.append(f'\t\t<CallsDevices>{escape_xml(cd)}</CallsDevices>')
        
    stype = clean_val(item.get('ServiceType'))
    if stype:
        lines.append(f'\t\t<ServiceType>{escape_xml(stype)}</ServiceType>')
    subtype = clean_val(item.get('ServiceSubtype'))
    if subtype:
        lines.append(f'\t\t<ServiceSubtype>{escape_xml(subtype)}</ServiceSubtype>')
        
    for field in ['WorkExperience', 'Place', 'WorkWithContract', 'Guarantee', 'WorkDays', 'WorkTimeFrom', 'WorkTimeTo']:
        val = clean_val(item.get(field))
        if val:
            lines.append(f'\t\t<{field}>{escape_xml(val)}</{field}>')
            
    plist = clean_val(item.get('PriceList'))
    if not plist and default_price_list:
        plist = default_price_list
    if plist:
        lines.append(f'\t\t<PriceList><![CDATA[{plist}]]></PriceList>')
        
    video = clean_val(item.get('VideoURL'))
    if video:
        lines.append(f'\t\t<VideoURL>{escape_xml(video)}</VideoURL>')
        
    lines.append('\t</Ad>')
    return '\n'.join(lines)

def convert_excel_to_xml(xlsx_path, xml_path, default_price_list=None, new_photos=None, shuffle_photos=False):
    ads = load_ads_from_excel(xlsx_path)
    xml_header = '<?xml version="1.0" encoding="utf-8"?>\n<Ads formatVersion="3" target="Avito.ru">\n'
    xml_footer = '\n</Ads>\n'
    
    ads_xml = []
    for item in ads:
        ads_xml.append(build_ad_xml(item, default_price_list=default_price_list, new_photos=new_photos, shuffle_photos=shuffle_photos))
        
    final_content = xml_header + '\n'.join(ads_xml) + xml_footer
    
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    print(f"[+] XML-файл успешно сохранён: '{xml_path}' (размер: {os.path.getsize(xml_path):,} байт)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Конвертация Excel объявлений Авито в XML-фид')
    parser.add_argument('--input', '-i', required=True, help='Путь к файлу Excel (.xlsx)')
    parser.add_argument('--output', '-o', default='avito_feed.xml', help='Имя выходного XML-файла')
    parser.add_argument('--pricelist', '-p', default=None, help='Прайс-лист для подстановки')
    parser.add_argument('--photos', default=None, help='Новые URL фото через |')
    parser.add_argument('--shuffle-photos', action='store_true', help='Перемешать доп. фото')
    args = parser.parse_args()
    
    convert_excel_to_xml(args.input, args.output, default_price_list=args.pricelist, new_photos=args.photos, shuffle_photos=args.shuffle_photos)
