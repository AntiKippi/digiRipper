# digiRipper
A small bash script to download books from digi4school in PDF format.

## Usage:

To use this script you first need to edit the configuration parameters.

### Parameters

The parameter `BOOK_NAME` specifies the name of the book. You can set it arbitrarily. The resulting PDF will have the book name as file name.

The parameter `BOOK_ID` is the ID of the book you want to download. It is located in the URL after /ebook/. 

The parameter `PAGES` specifies till which page you want to download this book. If you want to download the whole book press the go to last page button. Then the page count should also be located in the URL (after ?page=).

The parameter `COOKIE` is the hardest to set. It specifies the cookies which should be send to the server when downloading the book. To get it in the [Mozilla Firefox](https://www.mozilla.org/firefox/) browser, open the developer tools by pressing <kbd>F12</kbd> and go to the network tab. Then reload the page, select the first request popping up in the section below and search for the 'Cookie' field in the request headers on the right. Click on the value of this field and copy and paste this value into the `COOKIE` parameter.  
NOTE: You have to adapt the `COOKIE` parameter for every book you download.

The parameter `OUTPUT_DIRECTORY` specifies the directory in which the files should be downloaded. The resulting PDF file will also be located in this directory.  The directory should NOT be ended by a trailing /.  
NOTE: You can use other variables defined above in this parameter. For example if you set the `BOOK_ID` to 1234 then you can use this in the output directory by using `$BOOK_ID`. So `OUTPUT_DIRECTORY="/path/to/book/$BOOK_ID"` will result in `OUTPUT_DIRECTORY="/path/to/book/1234"`.

The parameter `CLEANUP` just specifies if the downloaded files should be removed after the PDF has been created. 0 means "No" and 1 means "Yes".

### Execution

If you have set all parameters you can now download your book by just running the script. This will create a PDF file containing the book in the directory specified by the `OUTPUT_DIRECTORY` variable.

## Dependencies

The script depends on the following programs:
- `wget` - Downloading the content from the website
- `rsvg-convert` - Combining the downloaded SVG files into a PDF

## Bugs

If you find a bug please just create a issue at this repository.

## Contributions

Thanks to [sk22](https://gist.github.com/sk22 "GitHub Gist Account of sk22") for inspiration and the base script. My work was made on top of his original script which he published at GitHub Gist. The original script can be viewed here: [https://gist.github.com/sk22/dabddad4af91154c55795568833ef984](https://gist.github.com/sk22/dabddad4af91154c55795568833ef984).
