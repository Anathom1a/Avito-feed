import sys, os, argparse, xml.etree.ElementTree as ET

def validate_avito_xml(xml_path):
    print(f'[*] Проверка фида: {xml_path}...')
    if not os.path.exists(xml_path):
        print(f'[-] Файл {xml_path} не найден!')
        return False
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f'[-] Ошибка XML синтаксиса: {e}')
        return False
    errors = []
    if root.tag != 'Ads' or root.get('formatVersion') != '3' or root.get('target') != 'Avito.ru':
        errors.append('Неверный корневой элемент <Ads formatVersion="3" target="Avito.ru">')
    ads = root.findall('Ad')
    if not ads:
        errors.append('Нет объявлений <Ad>')
    seen_ids = set()
    for idx, ad in enumerate(ads, 1):
        ad_id_el = ad.find('Id')
        if ad_id_el is None or not ad_id_el.text:
            errors.append(f'Объявление #{idx}: нет Id')
        else:
            ad_id = ad_id_el.text.strip()
            if ad_id in seen_ids: errors.append(f"Объявление #{idx}: дубликат Id '{ad_id}'")
            seen_ids.add(ad_id)
        for tag in ['Category', 'Title', 'Description', 'Address']:
            el = ad.find(tag)
            if el is None or not (el.text or '').strip():
                errors.append(f'Объявление #{idx}: отсутствует <{tag}>')
        imgs = ad.find('Images')
        if imgs is None or len(imgs.findall('Image')) == 0:
            errors.append(f'Объявление #{idx}: нет фото в <Images>')
    print(f'[+] Проверено {len(ads)} объявлений. Ошибок: {len(errors)}')
    if errors:
        for e in errors[:10]: print('  -', e)
        return False
    print('[+] ФИД ВАЛИДЕН ПО СТАНДАРТУ АВИТО v3!')
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('feed', nargs='?', default='avito_feed.xml')
    args = parser.parse_args()
    sys.exit(0 if validate_avito_xml(args.feed) else 1)
