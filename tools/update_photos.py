#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, argparse, random, xml.etree.ElementTree as ET

def update_photos(input_xml, output_xml, new_urls=None, shuffle=False):
    tree = ET.parse(input_xml)
    root = tree.getroot()
    ads = root.findall('Ad')
    url_list = [u.strip() for u in new_urls.split('|') if u.strip()] if new_urls else []
    for ad in ads:
        imgs = ad.find('Images')
        if imgs is None: imgs = ET.SubElement(ad, 'Images')
        target = list(url_list) if url_list else [i.get('url') for i in imgs.findall('Image') if i.get('url')]
        if shuffle and len(target) > 1:
            first, rest = target[0], target[1:]
            random.shuffle(rest)
            target = [first] + rest
        imgs.clear()
        for u in target[:10]:
            ET.SubElement(imgs, 'Image', url=u)
    tree.write(output_xml, encoding='utf-8', xml_declaration=True)
    print(f'[+] Обновлены фото в {len(ads)} объявлениях. Сохранено в: {output_xml}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', default='avito_feed.xml')
    parser.add_argument('-u', '--urls', default=None)
    parser.add_argument('--shuffle', action='store_true')
    args = parser.parse_args()
    update_photos(args.input, args.output, args.urls, args.shuffle)
