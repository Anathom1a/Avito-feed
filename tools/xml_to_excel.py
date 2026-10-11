#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, argparse, openpyxl, xml.etree.ElementTree as ET

EXCEL_HEADERS = [
    'Id', 'ListingFee', 'AvitoId', 'ManagerName', 'ContactPhone', 'ImageUrls', 
    'ImageNames', 'ContactMethod', 'Category', 'Price', 'Title', 'Description', 
    'Address', 'ServiceType', 'ServiceSubtype', 'WorkExperience', 'Place', 
    'WorkWithContract', 'Guarantee', 'WorkDays', 'WorkTimeFrom', 'WorkTimeTo', 
    'PriceList', 'AvitoDateEnd', 'CompanyName', 'AvitoStatus', 'EMail'
]

def xml_to_excel(xml_path, xlsx_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ads = root.findall('Ad')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Компьютерная пом-ОС и программы'
    ws.cell(1, 1).value = 'Услуги - Предложение услуг - Компьютерная помощь - ОС и программы'
    for c_idx, h in enumerate(EXCEL_HEADERS, 1): ws.cell(2, c_idx).value = h
    row3_map = {'Id': 'Обязательный', 'Category': 'Обязательный', 'Title': 'Обязательный', 'Description': 'Обязательный', 'Address': 'Обязательный', 'ServiceType': 'Обязательный', 'ServiceSubtype': 'Обязательный'}
    for c_idx, h in enumerate(EXCEL_HEADERS, 1): ws.cell(3, c_idx).value = row3_map.get(h, 'Необязательный'); ws.cell(4, c_idx).value = 'Подробнее о параметре'
    for r_idx, ad in enumerate(ads, start=5):
        imgs = [i.get('url') for i in ad.findall('Images/Image') if i.get('url')]
        for c_idx, h in enumerate(EXCEL_HEADERS, 1):
            cell = ws.cell(r_idx, c_idx)
            if h == 'ImageUrls': cell.value = ' | '.join(imgs)
            elif h == 'AvitoDateEnd': de = ad.find('DateEnd'); cell.value = de.text if de is not None else ''
            else: el = ad.find(h); cell.value = el.text if el is not None else ''
    wb.save(xlsx_path)
    print(f'[+] Экспорт в Excel: {xlsx_path} ({len(ads)} строк)')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', default='avito_ads_exported.xlsx')
    args = parser.parse_args()
    xml_to_excel(args.input, args.output)
