#!/bin/python3

######################################################
# openlibraryDownloader
# Script to download all books from digi4school.at open library
#
# Author: Kippi
# Version: 1.2
######################################################

# --- BEGIN IMPORTS (DO NOT EDIT) ---
import subprocess
import requests
import argparse
import signal
import time
import os
from pyquery import PyQuery
from pathlib import Path
# --- END IMPORTS

# --- BEGIN CONFIG ---

# Set the path to which the books should be downloaded
output_dir = ''

# Define if additionally to downloading the files they should be combined in a PDF file
generate_pdf = False

# Define if the cached extra files should be used
use_cache = True

# Define how often the script should retry after an error occurs
max_retries = 3

# Define how long the script should wait after an error occurred
error_timeout = 30

# --- END CONFIG ---

# DO NOT EDIT BELOW THIS LINE IF YOU DO NOT KNOW WHAT YOU ARE DOING


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
def download_content(content_node, book_url, cookies, dl_directory):
    extra_file = os.path.join(dl_directory, content_node('h1').text().replace('/', '-'))

    if use_cache and os.path.isfile(extra_file) and os.path.getsize(extra_file) > 0:
        return

    r = requests.get(book_url + content_node.attr['href'], headers=headers, cookies=cookies, stream=True)
    r.raise_for_status()
    with open(extra_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=16384):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


def download_content_from_directory(content_tree, directory_id, book_url, cookies, base_dir):
    # Mitigate error if selector contains a -
    directory_id = directory_id.replace('-', '\\-')

    for content_node in content_tree('a:not(.directory).sub.' + directory_id).items():
        download_content(content_node, book_url, cookies, base_dir)

    for dir_node in content_tree('a.directory.sub.' + directory_id).items():
        directory_path = os.path.join(base_dir, dir_node('h1').text().replace('/', '-'))
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        download_content_from_directory(content_tree, dir_node.attr['id'], book_url, cookies, directory_path)


def download_book(book_title, book_id, cookie_str, book_dir, book_response):
    Path(book_dir).mkdir(parents=True, exist_ok=True)
    book_head = PyQuery(book_response.text)('head')
    with open(os.path.join(book_dir, "info.txt"), "a", encoding=encoding) as f:
        f.write(os.linesep + u"Publisher Homepage: %s" % str(book_head('meta[name="publisherweb"]').attr['content']))
        f.write(os.linesep + u"Publisher Address: %s" % str(book_head('meta[name="publisheradr"]').attr['content']))
        f.write(os.linesep + u"Publisher Phone Number: %s" % str(book_head('meta[name="publishertel"]').attr['content']))
        f.write(os.linesep + u"Publisher E-Mail Address: %s" % str(book_head('meta[name="publishermail"]').attr['content']))
        f.write(os.linesep + u"Meta Title: %s" % str(book_head('meta[name="title"]').attr['content']))
        f.write(os.linesep + u"SBNr: %s" % str(book_head('meta[name="sbnr"]').attr['content']))

    if generate_pdf:
        return subprocess.run(['./digiRipper.sh', '-s', '-d', '-n', book_title, '-i', book_id, '-c', cookie_str, '-o', book_dir])
    else:
        return subprocess.run(['./digiRipper.sh', '-s', '-g', '-n', book_title, '-i', book_id, '-c', cookie_str, '-o', book_dir])


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
        print("Error after %d retries, skipping book..." % (retry_count - 1))
        return retry_end


def main():
    global output_dir, generate_pdf, use_cache, max_retries, error_timeout

    parser = argparse.ArgumentParser(description='A downloader for the digi4school open library')
    parser.add_argument('-s',
                        '--start',
                        type=float,
                        action='store',
                        dest='start',
                        default=0,
                        required=False,
                        help='Start the download at START percent')
    parser.add_argument('-e',
                        '--end',
                        type=float,
                        action='store',
                        dest='end',
                        default=100,
                        required=False,
                        help='Stop the download at END percent')
    parser.add_argument('-o',
                        '--output-directory',
                        type=str,
                        action='store',
                        dest='output_dir',
                        default=output_dir,
                        required=False,
                        help='The directory into which the books should be downloaded')
    parser.add_argument('-g',
                        '--generate-pdf',
                        action='store_true',
                        dest='generate_pdf',
                        required=False,
                        help='Generate a pdf when all files are downloaded')
    parser.add_argument('-ng',
                        '--no-generate-pdf',
                        action='store_false',
                        dest='generate_pdf',
                        required=False,
                        help='Do NOT generate a pdf when all files are downloaded')
    parser.add_argument('-u',
                        '--use-cache',
                        action='store_true',
                        dest='use_cache',
                        required=False,
                        help='Use already downloaded (cached) extra files')
    parser.add_argument('-nu',
                        '--no-use-cache',
                        action='store_false',
                        dest='use_cache',
                        required=False,
                        help='Download extra files again')
    parser.add_argument('-m',
                        '--max-retries',
                        type=int,
                        action='store',
                        dest='max_retries',
                        default=max_retries,
                        required=False,
                        help='Retry downloading MAX_RETRIES times before skipping the book')
    parser.add_argument('-t',
                        '--error-timeout',
                        type=float,
                        action='store',
                        dest='error_timeout',
                        default=error_timeout,
                        required=False,
                        help='Wait ERROR_TIMEOUT seconds before retrying the download')

    args = parser.parse_args()
    start = args.start
    end_percent = args.end
    output_dir = args.output_dir
    max_retries = args.max_retries
    error_timeout = args.error_timeout

    if args.generate_pdf is not None:
        generate_pdf = args.generate_pdf
    if args.use_cache is not None:
        use_cache = args.use_cache

    if len(output_dir) < 1:
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

    if start > 0:
        print("\nSkipping first %.2f %%..." % start)

    i = 0
    for book in books.items():
        if stop:
            stop_program()

        i += 1
        percent = (i * 100 / book_count)

        if percent < start:
            continue

        if percent > end_percent:
            print("Stopping at %.2f %% ..." % end_percent)
            break

        book_id = book.attr['data-id']
        title = book('h1').text().replace('/', '-')
        current_path = os.path.join(output_dir, book_id)
        Path(current_path).mkdir(parents=True, exist_ok=True)
        print('\n\nDownloading book "' + book_id + "\" (%.2f %%)" % percent)

        if generate_pdf:
            if os.path.isfile(os.path.join(current_path, title + '.pdf')):
                print('Found existing PDF skipping...')
                continue
        else:
            if os.path.isfile(os.path.join(current_path, 'generate-pdf.sh')):
                print('Found PDF generation script, skipping...')
                continue

        # Writing info about book
        with open(os.path.join(current_path, 'info.txt'), 'w', encoding=encoding) as f:
            f.writelines(os.linesep.join([
                u"Thumbnail: %s" % str(book('img').attr['src']),
                u"Title: %s" % str(book('h1').text()),
                u"Publisher: %s" % str(book('h2').text())
            ]))

        if stop:
            stop_program()

        count = 0
        end = 1
        orig_book_id = book_id
        while count < end:
            book_id = orig_book_id
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
                if len(location) < 1:
                    location = book_base_url + book_path + book_id + '/'
                    print('WARNING: Can\'t find book location in header, assuming ' + location)

                r = requests.get(location, headers=headers, cookies=cookie_request.cookies, allow_redirects=False)
                r.encoding = encoding
                if r.status_code == 200:
                    if 'IDRViewer' not in r.text and '<div id="content">' in r.text:
                        book_id += "/1"
                        print('Found extra content, setting book_id to ' + str(book_id))
                        print('Downloading extra content...')

                        book_content = PyQuery(r.text)("#content")
                        extra_path = os.path.join(current_path, 'extra')
                        extra_books = []
                        Path(extra_path).mkdir(parents=True, exist_ok=True)

                        # Download root files
                        for node in book_content('a:not(.sub):not(.directory)').items():
                            if not str(node.attr['href']).startswith('1/'):
                                thumbnail_location = str(node('img').attr['src'])
                                if thumbnail_location.endswith('thumbnails/1.jpg') and not thumbnail_location.startswith('http'):
                                    extra_books.append([str(node.attr['href']).replace('/index.html', ''), node('h1').text().replace('/', '-')])
                                else:
                                    download_content(node, location, cookie_request.cookies, extra_path)

                        if stop:
                            stop_program()

                        # Download content of all root directories
                        for root_dir_node in book_content('a:not(.sub).directory').items():
                            root_dir = os.path.join(extra_path, root_dir_node('h1').text().replace('/', '-'))
                            Path(root_dir).mkdir(parents=True, exist_ok=True)
                            download_content_from_directory(book_content, root_dir_node.attr['id'], location, cookie_request.cookies, root_dir)

                        if stop:
                            stop_program()

                        for extra_book in extra_books:
                            print('Downloading extra book "' + extra_book[0] + '"...')
                            r = requests.get(location + extra_book[0] + '/', headers=headers, cookies=cookie_request.cookies)
                            if 'IDRViewer' not in r.text:
                                print('WARNING: Extra book "' + extra_book[0] + '" looks weird (contains no "IDRViewer"! Skipping...')
                                continue
                            if download_book(extra_book[1], orig_book_id + '/' + extra_book[0], cookie_str, os.path.join(extra_path, extra_book[1]), r).returncode != 0:
                                end = handle_error('ERROR: Error running digiRipper!', count, end)
                                continue

                        print('Downloaded extra content to "' + extra_path + '"')
                        r = requests.get(location + "1/", headers=headers, cookies=cookie_request.cookies)
                else:
                    print('WARNING: Got wrong response code from book page, skipping check for extra material!')

                if stop:
                    stop_program()

                if download_book(title, book_id, cookie_str, current_path, r).returncode != 0:
                    end = handle_error('ERROR: Error running digiRipper!', count, end)
                    continue

            except Exception as e:
                end = handle_error('ERROR: An exception was thrown: ' + str(e), count, end)
                continue


base_url = 'https://digi4school.at/'
book_base_url = 'https://a.digi4school.at/'
book_path = 'ebook/'
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

if __name__ == '__main__':
    main()
