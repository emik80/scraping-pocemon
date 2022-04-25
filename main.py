import os
import gspread as gspread
import requests
from bs4 import BeautifulSoup
# import pyimgur
import imgbbpy
from pokemon_services_data import *
from oauth2client.service_account import ServiceAccountCredentials


url1 = 'https://www.cardrush-pokemon.jp/product-list?keyword=%E3%82%B9%E3%83%AA%E3%83%BC%E3%83%96&Submit=%E6%A4%9C%E7%B4%A2&page='
url2 = 'https://www.cardrush-pokemon.jp/product-list?keyword=%E3%83%97%E3%83%AC%E3%82%A4%E3%83%9E%E3%83%83%E3%83%88&Submit=%E6%A4%9C%E7%B4%A2&page='

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
}


def get_all_pages(url, prefix, count):
    # collect url pages

    for i in range(1, count + 1):
        r = requests.get(url=f'{url}{i}', headers=headers)
        with open(f'data/page_{prefix}{i}.html', 'w', encoding='utf-8') as f:
            f.write(r.text)


def get_items_links():
    # collect items urls to all_links.txt

    for filename in os.listdir('data'):
        with open(f'data/{filename}', encoding='utf-8') as f:
            src = f.read()

        soup = BeautifulSoup(src, 'lxml')
        pattern = 'https://www.cardrush-pokemon.jp/product/'
        for link in soup.find_all('a', href=True):
            if pattern in link['href']:
                with open('data/all_links.txt', 'a', encoding='utf-8') as result:
                    print(link['href'], file=result)


# def imgur_upload(url, title):
#     # upload image to imgur.com - But be careful: the upload limit is 40-45 images from one IP
#
#     im = pyimgur.Imgur(CLIENT_ID, CLIENT_SECRET)
#     uploaded_image = im.upload_image(url=url, title=title)
#     return uploaded_image.link


def imgbb_upload(url):
    # upload image to imgbb.com - no limits uploading

    client = imgbbpy.SyncClient(API_KEY)
    image = client.upload(url=url)
    return image.url


def img_title_formatter(title):
    # crop image title

    index = None
    if '【' in title:
        index = title.find('【')
    if index:
        title = title[:index]
    return title.strip()


def google_workbook_write(data):
    # write data in Google Spreadsheet

    credentials = ServiceAccountCredentials.from_json_keyfile_name(gcredentials, gscope)
    gc = gspread.authorize(credentials)
    wks = gc.open(gdocument).sheet1
    wks.append_row(data)


def collect_data(url):
    # get item title, price, image url

    print(f'***Proceeding URL {url}')
    r = requests.get(url=url, headers=headers).text
    soup = BeautifulSoup(r, 'lxml')

    title = img_title_formatter(soup.find(class_='goods_name').text)
    price = soup.find(id='pricech').text[:-1]
    image = soup.find('a', class_='item_image_box main_img_href', href=True)['href']
    # image_hosting_url = imgur_upload(url=image, title=title)
    image_hosting_url = imgbb_upload(url=image)
    data = [title, price, image_hosting_url, url.strip(), image]
    return data


def main():

    # Collect html-pages from target sites
    get_all_pages(url=url1, prefix=0, count=7)
    get_all_pages(url=url2, prefix=1, count=4)

    # Collect urls from pages
    get_items_links()

    # Create headline in Google Workbook
    google_workbook_write(data=['Item Title', 'Price', 'Image URL', 'Item URL', 'Original Image URL'])

    with open('data/all_links.txt', encoding='utf-8') as f:
        count = 1
        for line in f:
            data = collect_data(url=line.lstrip())
            try:
                google_workbook_write(data)
            except Exception as e:
                print(f'Oops!!! Error {e}. Item {count} from {line.lstrip()}')
            else:
                print(f'***Item {count} from 940 - OK')
            count += 1


if __name__ == '__main__':
    main()
