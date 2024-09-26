   
   
 # async def cmd_download_books(self):
    #     all_books = {}

    #     if not self.books:
    #         await self.get_library()

    #     for book in self.books:
    #         if book is not None:
    #             # breakpoint()
    #             print(book["item"]["title"])
    #             asin = book["item"]["asin"]
    #             raw_title = book["item"]["title"]
    #             title = raw_title.replace(" ", "_")
    #             all_books[asin] = title

    #             try:
    #                 re = self.get_download_url(self.generate_url(
    #                     COUNTRY_CODE, "download", asin), num_results=1000, response_groups="product_desc, product_attrs")
    #             except audible.exceptions.NetworkError as e:
    #                 ExternalError(self.get_download_url,
    #                               asin, e).show_error()
    #                 continue

    #             audible_response = requests.get(re, stream=True)
    #             if audible_response.ok:
    #                 with open(f'audiobooks/{title}.aax', 'wb') as f:
    #                     print("Downloading %s" % raw_title)

    #                     total_length = audible_response.headers.get(
    #                         'content-length')

    #                     if total_length is None:  # no content length header
    #                         f.write(audible_response.content)
    #                     else:
    #                         dl = 0
    #                         total_length = int(total_length)
    #                         print(total_length)
    #                         for data in audible_response.iter_content(chunk_size=4096):
    #                             dl += len(data)
    #                             f.write(data)
    #                             done = int(50 * dl / total_length)
    #                             sys.stdout.write("\r[%s%s]" % (
    #                                 '=' * done, ' ' * (50-done)))

    #                             sys.stdout.write(
    #                                 f"   {int(dl / total_length * 100)}%")
    #                             sys.stdout.flush()

    #                     f.write(audible_response.content)

    #             else:
    #                 print(audible_response.text)