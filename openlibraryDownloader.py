#!/bin/python3

######################################################
# openlibraryDownloader
# Script to download all books from digi4school.at open library
#
# Author: Kippi
# Version: 1.1
######################################################

# --- BEGIN IMPORTS (DO NOT EDIT) ---
import subprocess
import requests
import signal
import time
import os
from pyquery import PyQuery
from pathlib import Path
# --- END IMPORTS

# --- BEGIN CONFIG ---

# Set the path to which the books should be downloaded
output_dir = os.path.join(os.path.abspath(os.sep), 'path', 'to', 'your' 'directory')

# Define if additionaly to downloading the files they should be combined in a PDF file 
generate_pdf = False

# Define if the cached extra files should be used
use_cache = True

# Define how often the script should retry after an error occures
max_retries = 3

# Define how long the script should wait after an error occured
error_timeout = 30

# --- END CONFIG ---

# DO NOT EDIT BELOW THIS LINE IF YOU DO NOT KNOW WHAT YOU ARE DOING


base_url = 'https://digi4school.at/'
openshelf_path = 'br/openshelf'
token_path = 'token/'
target_cookie_name = 'digi4b'
encoding = "utf-8"
stop = False

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

    rs = requests.post(form_url, form_payload, headers=headers, allow_redirects=False)
    rs.encoding = encoding
    return rs


# Used to download extra material content from single <a> html node
def download_content(content_node, ebook_url, cookie_jar, dl_directory):
    fname = os.path.join(dl_directory, content_node('h1').text().replace('/', '-'))

    if use_cache and os.path.isfile(fname) and os.path.getsize(fname) > 0:
        return

    rs = requests.get(ebook_url + content_node.attr['href'], headers=headers, cookies=cookie_jar, stream=True)
    rs.raise_for_status()
    with open(fname, 'wb') as fn:
        for chunk in rs.iter_content(chunk_size=16384):
            if chunk:  # filter out keep-alive new chunks
                fn.write(chunk)


def download_content_from_directory(content_tree, directory_id, ebook_url, cookie_jar, base_dir):
    # Mitigate error if selector contains a -
    directory_id = directory_id.replace('-', '\\-')

    for content_node in content_tree('a:not(.directory).sub.' + directory_id).items():
        download_content(content_node, ebook_url, cookie_jar, base_dir)

    for dir_node in content_tree('a.directory.sub.' + directory_id).items():
        directory_path = os.path.join(base_dir, dir_node('h1').text().replace('/', '-'))
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        download_content_from_directory(content_tree, dir_node.attr['id'], ebook_url, cookie_jar, directory_path)


# Stop when receiving USR1 signal
def handle_usr1(signal_num, frame):
    global stop
    stop = True


def stop_program():
    print("Program stopped by user!")
    exit(0)


def handle_error(error_msg, retry_count, retry_end):
    print(error_msg)
    if retry_count <= max_retries:
        print("Waiting %d s and retrying (%d of %d)" % (error_timeout, retry_count, max_retries))
        time.sleep(error_timeout)
        return retry_end + 1
    else:
        print("Error after %d retries, skipping book..." % (count - 1))
        return retry_end


if output_dir == '':
    output_dir = input("Output directory: ")

Path(output_dir).mkdir(parents=True, exist_ok=True)

signal.signal(signal.SIGUSR1, handle_usr1)

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
    if stop:
        stop_program()

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

    if stop:
        stop_program()

    count = 0
    end = 1
    while count < end:
        count += 1
        try:
            cookie_request = send_form(send_form(requests.get(base_url + token_path + book_id, headers=headers)))
            cookie_str = ''
            for cookie in cookie_request.cookies:
                if cookie.name == target_cookie_name:
                    cookie_str = cookie.name + '=' + cookie.value + '; '

            if len(cookie_str) < 1:
                end = handle_error('ERROR: Cookie not found!', count, end)
                continue

            if stop:
                stop_program()

            location = cookie_request.headers['Location']
            if len(location) > 0:
                r = requests.get(location, headers=headers, cookies=cookie_request.cookies)
                r.encoding = encoding
                if 'IDRViewer' not in r.text and '<div id="content">' in r.text:
                    book_id += "/1"
                    print('Found extra content, setting book_id to ' + str(book_id))
                    print('Downloading extra content...')

                    book_content = PyQuery(r.text)("#content")
                    extra_path = os.path.join(current_path, 'extra')
                    Path(extra_path).mkdir(parents=True, exist_ok=True)

                    # Download root files
                    for node in book_content('a:not(.sub):not(.directory)').items():
                        if not str(node.attr['href']).startswith('1/'):
                            download_content(node, location, cookie_request.cookies, extra_path)

                    # Download content of all root directories
                    for root_dir_node in book_content('a:not(.sub).directory').items():
                        root_dir = os.path.join(extra_path, root_dir_node('h1').text().replace('/', '-'))
                        Path(root_dir).mkdir(parents=True, exist_ok=True)
                        download_content_from_directory(book_content, root_dir_node.attr['id'], location, cookie_request.cookies, root_dir)
                    print('Downloaded extra content to "' + extra_path + '"')

                    r = requests.get(location + "1/", headers=headers, cookies=cookie_request.cookies)

                ebook_head = PyQuery(r.text)('head')
                with open(os.path.join(current_path, "info.txt"), "a", encoding=encoding) as f:
                    f.write(os.linesep + u"Publisher Homepage: %s" % str(ebook_head('meta[name="publisherweb"]').attr['content']))
                    f.write(os.linesep + u"Publisher Address: %s" % str(ebook_head('meta[name="publisheradr"]').attr['content']))
                    f.write(os.linesep + u"Publisher Phone Number: %s" % str(ebook_head('meta[name="publishertel"]').attr['content']))
                    f.write(os.linesep + u"Publisher E-Mail Address: %s" % str(ebook_head('meta[name="publishermail"]').attr['content']))
                    f.write(os.linesep + u"SBNr: %s" % str(ebook_head('meta[name="sbnr"]').attr['content']))
            else:
                print('WARNING: Can\'t get Location header, skipping check for extra material!')

            if stop:
                stop_program()

            result = None
            if generate_pdf:
                result = subprocess.run(['./digiRipper.sh', '-s', '-d', '-n', title, '-i', book_id, '-c', cookie_str, '-o', current_path])
            else:
                result = subprocess.run(['./digiRipper.sh', '-s', '-g', '-n', title, '-i', book_id, '-c', cookie_str, '-o', current_path])

            if result.returncode != 0:
                end = handle_error('ERROR: Error running digiRipper!', count, end)
                continue

        except Exception as e:
            end = handle_error('ERROR: An exception was thrown: ' + str(e), count, end)
            continue
