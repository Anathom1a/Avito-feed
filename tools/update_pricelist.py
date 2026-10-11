#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, argparse, xml.etree.ElementTree as ET

DEFAULT_SERVICES = [
    'Установка операционной системы Windows / macOS||1000|Да|за услугу',
    'Установка офисных программ (MS Office, Word, Excel)||500|Да|за услугу',
    'Установка графических программ (Photoshop, CorelDRAW)||700|Да|за услугу',
    'Установка программ видеомонтажа (Premiere, DaVinci)||800|Да|за услугу',
    'Установка САПР и 3D-программ (AutoCAD, 3ds Max, Archicad)||1200|Да|за услугу',
    'Настройка программ для мебели и ЧПУ (Базис, Artcam, NC-Studio)||1500|Да|за услугу',
    'Настройка ЭЦП, КриптоПро и сертификатов для торгов и ФНС||1000|Да|за услугу',
    'Удаленная компьютерная помощь и диагностика||500|Да|за услугу'
]

def update_pricelist(input_xml, output_xml, text=None):
    tree = ET.parse(input_xml)
    root = tree.getroot()
    ads = root.findall('Ad')
    target = text.strip() if text else '
'.join(DEFAULT_SERVICES)
    for ad in ads:
        pl = ad.find('PriceList')
        if pl is None: pl = ET.SubElement(ad, 'PriceList')
        pl.text = target
    tree.write(output_xml, encoding='utf-8', xml_declaration=True)
    print(f'[+] Прайс-лист обновлен в {len(ads)} объявлениях. Сохранено в: {output_xml}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', default='avito_feed.xml')
    parser.add_argument('-t', '--text', default=None)
    args = parser.parse_args()
    update_pricelist(args.input, args.output, args.text)
