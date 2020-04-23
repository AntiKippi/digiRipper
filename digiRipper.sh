#!/bin/bash

######################################################
# digiRipper
# Script to download books from digi4school.at
#
# Author: Kippi
# Version: 1.2
######################################################

# --- BEGIN CONFIG ---

# Book name used for the name of the PDF file
BOOK_NAME=''

# book id, as in the url (after '/ebook/')
# (note that this is usually just one number, for example 2453), but it can also be muliple, like 2366/1)
BOOK_ID=

# Number of pages
# This is optional, if no value is given the total number of pages of the book will be guessed
PAGES=

# paste the cookie as it is send in the HTTP header (from your logged in browser page) between the two single quotes below
COOKIE=''

# Directory to which files should be downloaded
OUTPUT_DIRECTORY='/tmp/digi4school/$BOOK_ID'

# Define if the downloaded files should be cleaned up after the pdf was created
# 0 means "No", 1 means "Yes"
CLEANUP=1

# Define if the already downloaded files should be used
# Faster, but the available files might be invalid
# 0 means "No", 1 means "Yes"
USE_CACHED=1

# Define if the script shall promt to start the download
# 0 means "No", 1 means "Yes"
INTERACTIVE=1

# Define if a pdf file containing the book should be created or the files should be just downloaded
# 0 means "No", 1 means "Yes"
GENERATE_PDF=1

# --- END CONFIG ---

# DO NOT EDIT BELOW THIS LINE IF YOU DO NOT KNOW WHAT YOU ARE DOING


function print_help() {
  echo "USAGE: $(basename "$0") [-s] [-d] [-f] [-g] [-n <BOOK NAME>] [-i <BOOK ID>] [-c <COOKIE HEADER>] [-o <OUTPUT DIRECTORY] [-p PAGES]"
  echo
  echo "  -s  Be silent (non-interactive)"
  echo "  -d  Be dirty (do not cleanup)"
  echo "  -f  Use fresh files (do not use cache)"
  echo "  -g  Do not generate a pdf file (also implies -d)"
  echo
  echo "If no arguments are given the default parameters from the config will be used"
}

function wget_p() {
  wget -q -T 150 -t 2 --recursive --header="Cookie: $COOKIE" --header="Referer: $PROTOCOL$HOST/" --directory-prefix="$OUTPUT_DIRECTORY" --user-agent="Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0" "$1"
  return $?
}

function validate_svg() {
  xmllint --format "$1" &> /dev/null
  if [ $? != 0 ]; then
    rm -f "$1" &> /dev/null
    echo -e "$2"
    exit 1
  fi
}

# $1: URL
function get_filepath_from_url() {
  # Remove http:// or https:// from url to get file name
  filename="${1/http\:\/\//}"
  echo "$OUTPUT_DIRECTORY/${filename/https\:\/\//}"
}

#$1: URL, $2: Error message, $3: check svg error message (if empty no check will be done)
function download() {
  file=$(get_filepath_from_url "$1")

  if [ $USE_CACHED != 0 ] && [ -s "$file" ]; then
    return;
  fi

  wget_p "$1"
  errorcode=$?

  if [ $errorcode == 8 ] && [ -n "$4" ] && [ "$4" != 0 ]; then
    return $errorcode;
  fi

  if [ $errorcode != 0 ] || [ ! -s "$file" ]; then
    rm -f "$file" &> /dev/null
    echo -e "$2"
    exit 1
  fi

  if [ -n "$3" ]; then
    validate_svg "$file" "$3"
  fi
}


OPTIND=1         # Reset in case getopts has been used previously in the shell.

while getopts "hsdfgn:i:c:o:p:" opt; do
    case "$opt" in
    h)  # Print help and exit
        print_help
        exit 0
        ;;
    s)  # Silent (non-interactive)
        INTERACTIVE=0
        ;;
    d)  # Dirty (Don't cleanup)
        CLEANUP=0
        ;;
    f)  # Fresh (No cache)
        USE_CACHED=0
        ;;
    g)  # Generate no pdf
        GENERATE_PDF=0
        ;;
    n)  BOOK_NAME=$OPTARG
        ;;
    i)  BOOK_ID=$OPTARG
        ;;
    c)  COOKIE=$OPTARG
        ;;
    o)  OUTPUT_DIRECTORY=$OPTARG
        ;;
    p)  PAGES=$OPTARG
        ;;
    *)  echo "Unknown flag: $opt"
        echo
        print_help
        exit 1
    esac
done

shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift

if [ -z "$BOOK_ID" ] || [ -z "$COOKIE" ] || [ -z "$OUTPUT_DIRECTORY" ] || [ -z "$CLEANUP" ] || [ -z "$USE_CACHED" ] || [ -z "$GENERATE_PDF" ];  then
    echo "ERROR: One or more configuration parameters are missing!"
    exit 1
fi

OUTPUT_DIRECTORY=$(eval echo "$OUTPUT_DIRECTORY")
PROTOCOL='https://'
HOST='a.digi4school.at'
BASE_FOLDER="$HOST/ebook/$BOOK_ID"
BASE_URL="$PROTOCOL$BASE_FOLDER"
COOKIE_TEST_URL="$BASE_URL/1/1.svg"
PDF_GENERATION_SCRIPT_NAME="generate-pdf.sh"

svg_files=""

echo -n "book $BOOK_ID, "
if [ -z "$PAGES" ]; then
  echo "all pages"
else
  echo "$PAGES pages"
fi
echo

# DOWNLOAD PAGES

if [ $INTERACTIVE != 0 ]; then
    echo 'Press return to start the download.'
    read
fi;

mkdir -p "$OUTPUT_DIRECTORY"
cd "$OUTPUT_DIRECTORY" || (echo "Failed cd to $OUTPUT_DIRECTORY" && exit 1)

# Check if cookie was set correctly
cookie_test_file=$(get_filepath_from_url "$COOKIE_TEST_URL")
wget_p "$COOKIE_TEST_URL"
if [ $? != 0 ] || [ ! -s "$cookie_test_file" ]; then
  rm -f "$file" &> /dev/null
  echo "Error downloading test file ($COOKIE_TEST_URL)!"
  echo "Have you set your cookie correctly?"
  exit 1
fi

validate_svg "$cookie_test_file" "Error downloading $COOKIE_TEST_URL: $cookie_test_file is no valid SVG file! \nHave you set your cookie correctly?"

echo 'Downloading svg pages...'

if [ -z "$PAGES" ]; then
  i=0
  while true; do
    i=$(( i + 1 ))
    echo -ne "\rProgress: Page $PAGES"
    download "$BASE_URL/$i/$i.svg" "Error downloading $BASE_URL/$i/$i.svg!" "Error downloading $BASE_URL/$i/$i.svg: File is no valid SVG file!" 1
    if [ $? == 8 ]; then
      break;
    else
      PAGES=$i
      svg_files="$svg_files $OUTPUT_DIRECTORY/$BASE_FOLDER/$i/$i.svg"
    fi
  done
  PAGES=$(( PAGES - 1 ))
else
  for i in $(seq 1 $PAGES); do
    download "$BASE_URL/$i/$i.svg" "Error downloading $BASE_URL/$i/$i.svg!" "Error downloading $BASE_URL/$i/$i.svg: File is no valid SVG file!"
    svg_files="$svg_files $BASE_FOLDER/$i/$i.svg"
    percent=$(( (i * 100) / PAGES ))
    echo -ne "\rProgress: $percent%"
  done
fi

echo
echo 'Done downloading the pages.'


# DOWNLOAD IMAGES

echo
echo 'Downloading embedded images...'

for i in $(seq 1 $PAGES); do
  while read -r f ; do
    download "$BASE_URL/$i/$f" "Error downloading $BASE_URL/$i/$f!";
  done < <(grep -oP 'xlink:href="\K(.*?)\.png(?=")' "$OUTPUT_DIRECTORY/$BASE_FOLDER/$i/$i.svg")
  percent=$(( (i * 100) / PAGES ))
  echo -ne "\rProgress: $percent%"
done

echo
echo 'Done downloading the images.'

# Convert SVG files to PDF

echo
if [ $GENERATE_PDF != 0 ]; then
  echo 'Creating PDF...'

  rsvg-convert -f pdf -o "$OUTPUT_DIRECTORY/$BOOK_NAME.pdf" $svg_files;

  if [ $CLEANUP != 0 ]; then
      echo 'Cleaning up...'
      cleanup_dir="$OUTPUT_DIRECTORY/$HOST"
      rm -rf "${cleanup_dir:?}"
  fi

  echo "Done! The PDF has beed saved to \"$OUTPUT_DIRECTORY/$BOOK_NAME.pdf\""
else
  echo 'Creating PDF creation script...'

  echo "#!/bin/bash" > "$OUTPUT_DIRECTORY/$PDF_GENERATION_SCRIPT_NAME"
  echo >> "$OUTPUT_DIRECTORY/$PDF_GENERATION_SCRIPT_NAME"
  echo "rsvg-convert -f pdf -o \"$OUTPUT_DIRECTORY/$BOOK_NAME.pdf\" $svg_files;" >> "$OUTPUT_DIRECTORY/$PDF_GENERATION_SCRIPT_NAME"
  chmod 755 "$OUTPUT_DIRECTORY/$PDF_GENERATION_SCRIPT_NAME"

  echo "Done! To generate the PDF, run $PDF_GENERATION_SCRIPT_NAME"
fi
