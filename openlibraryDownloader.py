#!/bin/python3

######################################################
# openlibraryDownloader
# Script to download all books from digi4school.at open library
#
# Author: Kippi
# Version: 1.0
######################################################
import subprocess
import requests
import os
from pyquery import PyQuery
from pathlib import Path


output_dir = os.path.join(os.path.abspath(os.sep), 'path', 'to', 'your' 'directory')
generate_pdf = False
max_retries = 3

base_url = 'https://digi4school.at/'
openshelf_path = 'br/openshelf'
token_path = 'token/'
target_cookie_name = 'digi4b'
encoding = "utf-8"

get_all_books_payload = {'title': '%%%', 'publisher_id': '', 'level_of_education': ''}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0',
    'Accept': '*/*'
}


def send_form(form_request):
    form_html = PyQuery(form_request.text)('form')
    form_url = form_html.attr['action']
    form_payload = {}
    for item in form_html('input').items():
        form_payload[item.attr['name']] = item.attr['value']

    r = requests.post(form_url, form_payload, headers=headers, allow_redirects=False)
    r.encoding = encoding
    return r


if output_dir == '':
    output_dir = input("Output directory: ")

Path(output_dir).mkdir(parents=True, exist_ok=True)

r = requests.post(base_url + openshelf_path, get_all_books_payload, headers=headers)
r.encoding = encoding
books = PyQuery(r.text)('#shelf').find('a')
book_count = len(books)

print()
print(str(book_count) + ' books')
print("Output directory: " + output_dir)
input('Press [ENTER] to start the download')

i = 0
for book in books.items():
    i += 1
    book_id = book.attr['data-id']
    title = book('h1').text().replace('/', '-')
    current_path = os.path.join(output_dir, book_id)
    Path(current_path).mkdir(parents=True, exist_ok=True)
    print('\n\nDownloading book "' + book_id + "\" (%.2f %%)" % (i * 100 / book_count))

    if generate_pdf:
        if os.path.isfile(os.path.join(current_path, title + '.pdf')):
            print("Found existing PDF skipping...")
            continue
    else:
        if os.path.isfile(os.path.join(current_path, 'generate-pdf.sh')):
            print("Found PDF generation script, skipping...")
            continue

    # Writing info about book
    with open(os.path.join(current_path, "info.txt"), "w", encoding=encoding) as f:
        f.writelines(os.linesep.join([
            u"Thumbnail: %s" % str(book('img').attr['src']),
            u"Title: %s" % str(book('h1').text()),
            u"Publisher: %s" % str(book('h2').text())
        ]))
        f.close()

    count = 1
    while count <= max_retries:
        cookie_request = send_form(send_form(requests.get(base_url + token_path + book_id, headers=headers)))
        cookie_str = ''
        for cookie in cookie_request.cookies:
            if cookie.name == target_cookie_name:
                cookie_str = cookie.name + '=' + cookie.value + '; '

        if cookie_str == '':
            print("ERROR: Cookie not found, retrying (%d of %d)" % (count, max_retries))
            count += 1
            continue

        if generate_pdf:
            result = subprocess.run(['./digiRipper.sh', '-s', '-d', '-n', title, '-i', book_id, '-c', cookie_str, '-o', current_path])
        else:
            result = subprocess.run(['./digiRipper.sh', '-s', '-g', '-n', title, '-i', book_id, '-c', cookie_str, '-o', current_path])

        if result.returncode != 0:
            print("ERROR: Error running digiRipper, retrying (%d of %d)" % (count, max_retries))
            count += 1
            continue

        location = cookie_request.headers['Location']
        if len(location) > 0:
            r = requests.get(location, headers=headers, cookies=cookie_request.cookies)
            r.encoding = encoding
            ebook_head = PyQuery(r.text)('head')
            with open(os.path.join(current_path, "info.txt"), "a", encoding=encoding) as f:
                f.write(os.linesep + u"Publisher Homepage: %s" % str(ebook_head('meta[name="publisherweb"]').attr['content']))
                f.write(os.linesep + u"Publisher Address: %s" % str(ebook_head('meta[name="publisheradr"]').attr['content']))
                f.write(os.linesep + u"Publisher Phone Number: %s" % str(ebook_head('meta[name="publishertel"]').attr['content']))
                f.write(os.linesep + u"Publisher E-Mail Address: %s" % str(ebook_head('meta[name="publishermail"]').attr['content']))
                f.close()

        break
