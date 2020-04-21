# digiRipper
A small bash script to download books from digi4school in PDF format.

## Usage:

To use this script you first need to edit the configuration parameters or pass command line arguments.

### Command Line Arguments

Usage: `digiRipper.sh [-s] [-d] [-f] [-n <BOOK NAME>] [-i <BOOK ID>] [-c <COOKIE HEADER>] [-o <OUTPUT DIRECTORY] [-p ]`

`-s`: Be silent (non-interactive)  
`-d`: Be dirty (do not cleanup)  
`-f`: Use fresh files (do not use cache)  
`-n <BOOK NAME>`: The name of the book, used for the resulting PDF file name.  
`-i <BOOK ID>]`: The ID of the book you want to download  
`-c <COOKIE HEADER>`: The cookies as string, as they are send in the header of the http request(see parameter `COOKIE`)  
`-o <OUTPUT DIRECTORY`: The directory in which the book should be downloaded (see parameter `OUTPUT_DIRECTORY`). WARNING: Because you can use other variables in this parameter, like $BOOK_ID, this value is prone to command injection!  
`-p <PAGES>`: The number of pages you want to download.

If no arguments are given the default parameters from the config will be used

### Parameters

The parameter `BOOK_NAME` specifies the name of the book. You can set it arbitrarily. The resulting PDF will have the book name as file name.

The parameter `BOOK_ID` is the ID of the book you want to download. It is located in the URL after /ebook/. 

The parameter `PAGES` specifies till which page you want to download this book. If you want to download the whole book leave the parameter emtpy. Then the script will try guess the number of pages of the book. Alternatively you can get this value by pressing the go to last page button in the digi4school book. Then the page count should also be located in the URL (after ?page=).

The parameter `COOKIE` is the hardest to set. It specifies the cookies which should be send to the server when downloading the book. To get it in the [Mozilla Firefox](https://www.mozilla.org/firefox/) browser, open the developer tools by pressing <kbd>F12</kbd> and go to the network tab. Then reload the page, select the first request popping up in the section below and search for the 'Cookie' field in the request headers on the right. Click on the value of this field and copy and paste this value into the `COOKIE` parameter.  
NOTE: You have to adapt the `COOKIE` parameter for every book you download.

The parameter `OUTPUT_DIRECTORY` specifies the directory in which the files should be downloaded. The resulting PDF file will also be located in this directory.  The directory should NOT be ended by a trailing /.  
NOTE: You can use other variables defined above in this parameter. For example if you set the `BOOK_ID` to 1234 then you can use this in the output directory by using `$BOOK_ID`. So `OUTPUT_DIRECTORY="/path/to/book/$BOOK_ID"` will result in `OUTPUT_DIRECTORY="/path/to/book/1234"`.

The parameter `CLEANUP` specifies if the downloaded files should be removed after the PDF has been created.

The parameter `USE_CACHED` specifies if already downloaded files should be used. This might be faster but can lead to errors if a cached file is invalid, so turn it off if you experience errors.

The parameter `INTERACTIVE` specifies if the script should be interactive or not (prompt for confirmation before starting download)

### Execution

If you have set all parameters you can now download your book by just running the script. This will create a PDF file containing the book in the directory specified by the `OUTPUT_DIRECTORY` variable. You can also pass the values for the parameters via command line arguments.

## Dependencies

The script depends on the following programs:
- `wget` - Downloading the content from the website
- `rsvg-convert` - Combining the downloaded SVG files into a PDF
- `xmllint` - Validating downloaded SVG files

## Bugs

If you find a bug please just create a issue at this repository.

## Contributions

Thanks to [sk22](https://gist.github.com/sk22 "GitHub Gist Account of sk22") for inspiration and the base script. My work was made on top of his original script which he published at GitHub Gist. The original script can be viewed here: [https://gist.github.com/sk22/dabddad4af91154c55795568833ef984](https://gist.github.com/sk22/dabddad4af91154c55795568833ef984).
