#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для массового добавления или удаления ссылок на видео (<VideoURL>) в XML-фиде Авито.
Поддерживает YouTube, RuTube, VK Видео.
"""

import sys
import os
import argparse
import random
import xml.etree.ElementTree as ET

def update_videos(input_xml, output_xml, video_url=None, urls_file=None, clear=False):
    tree = ET.parse(input_xml)
    root = tree.getroot()
    ads = root.findall('Ad')
    print(f"[*] Открыт XML-фид: '{input_xml}', найдено {len(ads)} объявлений.")
    
    video_list = []
    if urls_file and os.path.exists(urls_file):
        with open(urls_file, 'r', encoding='utf-8') as f:
            video_list = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        print(f"[+] Загружено {len(video_list)} ссылок на видео из файла.")
    elif video_url:
        video_list = [u.strip() for u in video_url.split('|') if u.strip()]
        
    updated = 0
    for idx, ad in enumerate(ads):
        video_el = ad.find('VideoURL')
        if clear:
            if video_el is not None:
                ad.remove(video_el)
                updated += 1
            continue
            
        target_url = ''
        if video_list:
            target_url = video_list[idx % len(video_list)]
            
        if target_url:
            if video_el is None:
                video_el = ET.SubElement(ad, 'VideoURL')
            video_el.text = target_url
            updated += 1
            
    tree.write(output_xml, encoding='utf-8', xml_declaration=True)
    if clear:
        print(f"[+] Видео удалено из {updated} объявлений.")
    else:
        print(f"[+] Видео добавлено/обновлено в {updated} объявлениях.")
    print(f"[+] Сохранено в: '{output_xml}'")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Массовое управление ссылками на видео в фиде Авито')
    parser.add_argument('-i', '--input', required=True, help='Входной XML файл')
    parser.add_argument('-o', '--output', default='avito_feed.xml', help='Выходной XML файл')
    parser.add_argument('-u', '--url', default=None, help='URL видео (или несколько через |)')
    parser.add_argument('-f', '--file', default=None, help='Файл со списком ссылок на видео')
    parser.add_argument('--clear', action='store_true', help='Удалить видео из всех объявлений')
    args = parser.parse_args()
    
    update_videos(args.input, args.output, video_url=args.url, urls_file=args.file, clear=args.clear)
