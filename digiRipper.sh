#!/bin/bash

######################################################
# digiRipper
# Script to download books from digi4school.at
#
# Author: Kippi
# Version: 1.1
######################################################

# --- BEGIN CONFIG ---

# Book name used for the name of the PDF file
BOOK_NAME=''

# book id, as in the url (after '/ebook/')
# (note that this is usually just one number, for example 2453), but it can also be muliple, like 2366/1)
BOOK_ID=

# Number of pages
PAGES=

# paste your cookie (from your logged in browser page) between the two single quotes below
COOKIE=''

# Directory to which files should be downloaded
OUTPUT_DIRECTORY="/tmp/digi4school/$BOOK_ID"

# Define if the downloaded files should be cleaned up after the pdf was created
# 0 means "No", 1 means "Yes"
CLEANUP=1

# Define if the already downloaded files should be used
# Faster, but the available files might be invalid
# 0 means "No", 1 means "Yes"
USE_CACHED=1

# --- END CONFIG ---

# DO NOT EDIT BELOW THIS LINE IF YOU DO NOT KNOW WHAT YOU ARE DOING

if [ -z "$PAGES" ] || [ -z "$BOOK_ID" ] || [ -z "$COOKIE" ] || [ -z "$OUTPUT_DIRECTORY" ] || [ -z "$CLEANUP" ] || [ -z "$USE_CACHED" ]; then
    echo "ERROR: One or more configuration parameters are missing!"
    exit 1
fi

PROTOCOL='https://'
HOST='a.digi4school.at'
BASE_FOLDER="$HOST/ebook/$BOOK_ID"
BASE_URL="$PROTOCOL$BASE_FOLDER"
COOKIE_TEST_URL="$BASE_URL/1/1.svg"

# Remove http:// or https:// from url to get file name
COOKIE_TEST_FILE="${COOKIE_TEST_URL/http\:\/\//}"
COOKIE_TEST_FILE="${COOKIE_TEST_URL/https\:\/\//}"
COOKIE_TEST_FILE="$OUTPUT_DIRECTORY/$COOKIE_TEST_FILE"

echo $COOKIE_TEST_FILE

interactive=1
svg_files=""

OPTIND=1         # Reset in case getopts has been used previously in the shell.

while getopts "sdf" opt; do
    case "$opt" in
    s)  # Silent (non-interactive)
        interactive=0
        ;;
    d)  # Dirty (Don't cleanup)
        CLEANUP=0
        ;;
    f)  # Fresh (No cache)
        USE_CACHED=0
    esac
done

shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift


function wget_p() {
  wget -q --recursive --header="Cookie: $COOKIE" --header="Referer: $PROTOCOL$HOST/" --directory-prefix="$OUTPUT_DIRECTORY" --user-agent="Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0" "$1"
}

function download() {
  # Remove http:// or https:// from url to get file name
  file="${1/http\:\/\//}"
  file="${file/https\:\/\//}"


  if [ $USE_CACHED != 0 ] && [ -f "$OUTPUT_DIRECTORY/$BASE_FOLDER/$i/$i.svg" ]; then
    return;
  fi

  wget_p "$1"
  if [ $? != 0 ] || [ ! -f "$OUTPUT_DIRECTORY/$file" ] || [ ! -s "$OUTPUT_DIRECTORY/$BASE_FOLDER/1/1.svg" ]; then
    rm -f "$OUTPUT_DIRECTORY/$file" &> /dev/null
    echo "Error downloading \"$1\"!"
    exit 1
  fi
}


echo book $BOOK_ID, $PAGES pages
echo

# DOWNLOAD PAGES

if (($interactive > 0)); then
    echo 'Press return to start the download.'
    read
fi;

mkdir -p "$OUTPUT_DIRECTORY"
cd "$OUTPUT_DIRECTORY"

# Check if cookie was set correctly
wget_p "$COOKIE_TEST_URL"
if [ ! -f "$COOKIE_TEST_FILE" ] || [ ! -s "$COOKIE_TEST_FILE" ]; then
  rm -f "$COOKIE_TEST_FILE" &> /dev/null
  echo "Error downloading test file ($COOKIE_TEST_URL)!"
  echo "Have you set your cookie correctly?"
  exit 1
fi

xmllint --format "$COOKIE_TEST_FILE" &> /dev/null
if [ $? != 0 ]; then
  rm -f "$COOKIE_TEST_FILE" &> /dev/null
  echo "ERROR: \"$COOKIE_TEST_FILE\" is no valid SVG file!"
  echo "Have you set your cookie correctly?"
  exit 1
fi

echo 'Downloading svg pages...'

for i in $(seq 1 $PAGES); do
  download "$BASE_URL/$i/$i.svg"

  xmllint --format "$OUTPUT_DIRECTORY/$BASE_FOLDER/$i/$i.svg" &> /dev/null
  if [ $? != 0 ]; then
    rm -f "$OUTPUT_DIRECTORY/$BASE_FOLDER/$i/$i.svg"
    echo "Error downloading $BASE_URL/$i/$i.svg: File is no valid SVG file!"
    exit 1
  fi

  svg_files="$svg_files $OUTPUT_DIRECTORY/$BASE_FOLDER/$i/$i.svg"
  percent=$(( (i * 100) / PAGES ))
  echo -ne "\rProgress: $percent%"
done

echo
echo 'Done downloading the pages.'


# DOWNLOAD IMAGES

echo
echo 'Downloading embedded images...'

for i in $(seq 1 $PAGES); do
  cat "$OUTPUT_DIRECTORY/$BASE_FOLDER/$i/$i.svg" |
  grep -oP 'xlink:href="\K(.*?)\.png(?=")' |
  for f in $(</dev/stdin); do
    download "$BASE_URL/$i/$f";
  done
  percent=$(( (i * 100) / PAGES ))
  echo -ne "\rProgress: $percent%"
done

echo
echo 'Done downloading the images.'

# Convert SVG files to PDF

echo
echo 'Creating PDF...'

rsvg-convert -f pdf -o "$OUTPUT_DIRECTORY/$BOOK_NAME.pdf" $svg_files

if [ $CLEANUP != 0 ]; then
    echo 'Cleaning up...'
    rm -rf "$OUTPUT_DIRECTORY/$HOST"
fi;

echo "Done! The PDF has beed saved to \"$OUTPUT_DIRECTORY/$BOOK_NAME.pdf\""