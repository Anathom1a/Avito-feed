#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конвертер объявлений Авито из Excel (.xlsx) в XML-фид (формат v3 Avito.ru).
Строго соответствует официальной документации Авито 2026:
- PriceList со структурой <Service><ServiceName>...<ServicePrice>...
- Place и WorkDays со структурой <Option>...
- CDATA для описания <Description>
- Корректный порядок и вложенность тегов
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

def escape_xml(s):
    if not s:
        return ''
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

def parse_pricelist_string(pl_str):
    """
    Разбирает строку прайс-листа формата:
    ServiceName|ServiceTitle|ServicePrice|ServiceStartingPrice|ServicePriceType
    """
    if not pl_str:
        return []
    lines = [l.strip() for l in pl_str.split('\n') if l.strip()]
    services = []
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        # Дополняем до 5 элементов
        while len(parts) < 5:
            parts.append('')
            
        s_name = parts[0]
        s_title = parts[1]
        s_price = parts[2]
        s_starting = parts[3]
        s_type = parts[4] or 'за услугу'
        
        # Если s_name пустой, но есть s_title
        if not s_name and s_title:
            s_name = 'Своя услуга'
            
        if s_name:
            services.append({
                'ServiceName': s_name,
                'ServiceTitle': s_title,
                'ServicePrice': s_price,
                'ServiceStartingPrice': s_starting,
                'ServicePriceType': s_type
            })
    return services[:50] # Максимум 50 услуг

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

def build_ad_xml(item, default_price_list=None, new_photos=None, shuffle_photos=False):
    lines = ['\t<Ad>']
    
    # 1. Id
    ad_id = clean_val(item.get('Id'))
    lines.append(f'\t\t<Id>{escape_xml(ad_id)}</Id>')
    
    # 2. DateBegin / DateEnd
    db = clean_val(item.get('DateBegin'))
    if db:
        lines.append(f'\t\t<DateBegin>{escape_xml(db)}</DateBegin>')
        
    de = clean_val(item.get('DateEnd') or item.get('AvitoDateEnd'))
    if de:
        lines.append(f'\t\t<DateEnd>{escape_xml(de)}</DateEnd>')
        
    # 3. ListingFee (Package / PackageBBL / BBL)
    fee = clean_val(item.get('ListingFee')) or 'Package'
    lines.append(f'\t\t<ListingFee>{escape_xml(fee)}</ListingFee>')
    
    # 4. AdStatus
    status = clean_val(item.get('AdStatus'))
    if status:
        lines.append(f'\t\t<AdStatus>{escape_xml(status)}</AdStatus>')
        
    # 5. AvitoId
    avito_id = clean_val(item.get('AvitoId'))
    if avito_id:
        lines.append(f'\t\t<AvitoId>{escape_xml(avito_id)}</AvitoId>')
        
    # 6. ManagerName
    manager = clean_val(item.get('ManagerName'))
    if manager:
        lines.append(f'\t\t<ManagerName>{escape_xml(manager[:40])}</ManagerName>')
        
    # 7. ContactPhone
    phone = clean_val(item.get('ContactPhone'))
    if phone:
        lines.append(f'\t\t<ContactPhone>{escape_xml(phone)}</ContactPhone>')
        
    # 8. Images
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
        for u in urls[:10]: # До 10 фотографий
            lines.append(f'\t\t\t<Image url="{escape_xml(u)}"/>')
        lines.append('\t\t</Images>')
        
    # 9. ContactMethod
    cm = clean_val(item.get('ContactMethod')) or 'По телефону и в сообщениях'
    lines.append(f'\t\t<ContactMethod>{escape_xml(cm)}</ContactMethod>')
    
    # 10. Promo
    promo = clean_val(item.get('Promo'))
    if promo:
        lines.append(f'\t\t<Promo>{escape_xml(promo)}</Promo>')
        p_auto = clean_val(item.get('PromoAutoOptions'))
        if p_auto:
            lines.append('\t\t<PromoAutoOptions>')
            lines.append(f'\t\t\t<Item><Budget>{escape_xml(p_auto)}</Budget></Item>')
            lines.append('\t\t</PromoAutoOptions>')
        p_manual = clean_val(item.get('PromoManualOptions'))
        if p_manual:
            parts = p_manual.split('|')
            bid = parts[0].strip() if len(parts) > 0 else '1000'
            limit = parts[1].strip() if len(parts) > 1 else '10000'
            lines.append('\t\t<PromoManualOptions>')
            lines.append(f'\t\t\t<Item><Bid>{escape_xml(bid)}</Bid><DailyLimit>{escape_xml(limit)}</DailyLimit></Item>')
            lines.append('\t\t</PromoManualOptions>')
            
    # 11. Category
    cat = clean_val(item.get('Category')) or 'Предложение услуг'
    lines.append(f'\t\t<Category>{escape_xml(cat)}</Category>')
    
    # 12. Price
    price = clean_val(item.get('Price'))
    if price:
        lines.append(f'\t\t<Price>{escape_xml(price)}</Price>')
        
    # 13. Title (до 100 символов)
    title = clean_val(item.get('Title'))
    lines.append(f'\t\t<Title>{escape_xml(title[:100])}</Title>')
    
    # 14. Description с CDATA
    desc = clean_val(item.get('Description'))
    if desc:
        lines.append(f'\t\t<Description><![CDATA[{desc}]]></Description>')
    else:
        lines.append('\t\t<Description></Description>')
        
    # 15. Address / Coordinates
    address = clean_val(item.get('Address'))
    if address:
        lines.append(f'\t\t<Address>{escape_xml(address[:256])}</Address>')
        
    lat = clean_val(item.get('Latitude'))
    if lat:
        lines.append(f'\t\t<Latitude>{escape_xml(lat)}</Latitude>')
    lon = clean_val(item.get('Longitude'))
    if lon:
        lines.append(f'\t\t<Longitude>{escape_xml(lon)}</Longitude>')
        
    # 16. InternetCalls / CallsDevices
    ic = clean_val(item.get('InternetCalls'))
    if ic:
        lines.append(f'\t\t<InternetCalls>{escape_xml(ic)}</InternetCalls>')
    cd = clean_val(item.get('CallsDevices'))
    if cd:
        lines.append('\t\t<CallsDevices>')
        for dev in cd.split('|'):
            if dev.strip():
                lines.append(f'\t\t\t<Option>{escape_xml(dev.strip())}</Option>')
        lines.append('\t\t</CallsDevices>')
        
    # 17. ServiceType & ServiceSubtype
    stype = clean_val(item.get('ServiceType')) or 'Компьютерная помощь'
    lines.append(f'\t\t<ServiceType>{escape_xml(stype)}</ServiceType>')
    subtype = clean_val(item.get('ServiceSubtype')) or 'ОС и программы'
    lines.append(f'\t\t<ServiceSubtype>{escape_xml(subtype)}</ServiceSubtype>')
    
    # 18. WorkExperience
    exp = clean_val(item.get('WorkExperience'))
    if exp:
        lines.append(f'\t\t<WorkExperience>{escape_xml(exp)}</WorkExperience>')
        
    # 19. Place (многозначный параметр через <Option>)
    place = clean_val(item.get('Place'))
    if place:
        lines.append('\t\t<Place>')
        for opt in place.split('|'):
            if opt.strip():
                lines.append(f'\t\t\t<Option>{escape_xml(opt.strip())}</Option>')
        lines.append('\t\t</Place>')
        
    # 20. WorkWithContract & Guarantee
    contract = clean_val(item.get('WorkWithContract'))
    if contract:
        lines.append(f'\t\t<WorkWithContract>{escape_xml(contract)}</WorkWithContract>')
        
    guarantee = clean_val(item.get('Guarantee'))
    if guarantee:
        lines.append(f'\t\t<Guarantee>{escape_xml(guarantee)}</Guarantee>')
        
    # 21. WorkDays (многозначный параметр через <Option>)
    work_days = clean_val(item.get('WorkDays'))
    if work_days:
        lines.append('\t\t<WorkDays>')
        for d in work_days.split('|'):
            if d.strip():
                lines.append(f'\t\t\t<Option>{escape_xml(d.strip())}</Option>')
        lines.append('\t\t</WorkDays>')
        
    # 22. WorkTimeFrom & WorkTimeTo
    time_from = clean_val(item.get('WorkTimeFrom'))
    if time_from:
        lines.append(f'\t\t<WorkTimeFrom>{escape_xml(time_from)}</WorkTimeFrom>')
    time_to = clean_val(item.get('WorkTimeTo'))
    if time_to:
        lines.append(f'\t\t<WorkTimeTo>{escape_xml(time_to)}</WorkTimeTo>')
        
    # 23. PriceList - вложенные элементы <Service>
    plist_raw = clean_val(item.get('PriceList'))
    if not plist_raw and default_price_list:
        plist_raw = default_price_list
        
    services = parse_pricelist_string(plist_raw)
    if services:
        lines.append('\t\t<PriceList>')
        for s in services:
            lines.append('\t\t\t<Service>')
            lines.append(f'\t\t\t\t<ServiceName>{escape_xml(s["ServiceName"])}</ServiceName>')
            if s.get('ServiceTitle'):
                lines.append(f'\t\t\t\t<ServiceTitle>{escape_xml(s["ServiceTitle"])}</ServiceTitle>')
            if s.get('ServicePrice'):
                lines.append(f'\t\t\t\t<ServicePrice>{escape_xml(s["ServicePrice"])}</ServicePrice>')
            if s.get('ServiceStartingPrice') in ['Да', 'True', 'true', '1']:
                lines.append('\t\t\t\t<ServiceStartingPrice>Да</ServiceStartingPrice>')
            s_type = s.get('ServicePriceType') or 'за услугу'
            lines.append(f'\t\t\t\t<ServicePriceType>{escape_xml(s_type)}</ServicePriceType>')
            lines.append('\t\t\t</Service>')
        lines.append('\t\t</PriceList>')
        
    # 24. VideoURL
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
    parser = argparse.ArgumentParser(description='Конвертация Excel объявлений Авито в XML-фид по официальной спецификации v3')
    parser.add_argument('--input', '-i', required=True, help='Путь к файлу Excel (.xlsx)')
    parser.add_argument('--output', '-o', default='avito_feed.xml', help='Имя выходного XML-файла')
    parser.add_argument('--pricelist', '-p', default=None, help='Прайс-лист для подстановки')
    parser.add_argument('--photos', default=None, help='Новые URL фото через |')
    parser.add_argument('--shuffle-photos', action='store_true', help='Перемешать доп. фото')
    args = parser.parse_args()
    
    convert_excel_to_xml(args.input, args.output, default_price_list=args.pricelist, new_photos=args.photos, shuffle_photos=args.shuffle_photos)
