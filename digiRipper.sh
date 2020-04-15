#!/bin/bash

######################################################
# digiRipper
# Script to download books from digi4school.at
#
# Author: Kippi
######################################################

# --- BEGIN CONFIG ---

# Book name used for the name of the pdf file
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

# --- END CONFIG ---

# DO NOT EDIT BELOW THIS LINE IF YOU DO NOT KNOW WHAT YOU ARE DOING

if [ -z "$PAGES" ] || [ -z "$BOOK_ID" ] || [ -z "$COOKIE" ] || [ -z "$OUTPUT_DIRECTORY" ]; then
    echo "ERROR: One or more configuration parameters are missing!"
    exit 1
fi

PROTOCOL='https://'
HOST='a.digi4school.at'
BASE_FOLDER="$HOST/ebook/$BOOK_ID"
BASE_URL="$PROTOCOL$BASE_FOLDER"

interactive=1
svg_files=""

OPTIND=1         # Reset in case getopts has been used previously in the shell.

while getopts "qd" opt; do
    case "$opt" in
    q)
        interactive=0
        ;;
    d)
        CLEANUP=0
    esac
done

shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift


echo book $BOOK_ID, $PAGES pages
echo

# DOWNLOAD PAGES

if (($interactive > 0)); then
    echo 'Press return to start the download.'
    read
fi;

mkdir -p "$OUTPUT_DIRECTORY"
cd "$OUTPUT_DIRECTORY"

echo 'Downloading svg pages...'

for i in $(seq 1 $PAGES); do
  wget --recursive --header="Cookie: $COOKIE" --header="Referer: $PROTOCOL$HOST/" --directory-prefix="$OUTPUT_DIRECTORY" --user-agent="Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0" -q "$BASE_URL/$i/$i.svg"
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
    wget --recursive --header="Cookie: $COOKIE" --header="Referer: $PROTOCOL$HOST/" --directory-prefix="$OUTPUT_DIRECTORY" --user-agent="Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0" -q "$BASE_URL/$i/$f";
  done
  percent=$(( (i * 100) / PAGES ))
  echo -ne "\rProgress: $percent%"
done

echo
echo 'Done downloading the images.'

# Convert svg files to pdf

echo
echo 'Creating pdf...'

rsvg-convert -f pdf -o "$OUTPUT_DIRECTORY/$BOOK_NAME.pdf" $svg_files

if (($CLEANUP > 0)); then
    echo 'Cleaning up...'
    rm -rf "$OUTPUT_DIRECTORY/$HOST"
fi;

echo "Done! The pdf has beed saved to \"$OUTPUT_DIRECTORY/$BOOK_NAME.pdf\""