import asyncio
import audible
import requests

import sys

country_code_mapping = {
    "us": ".com",
    "ca": ".ca",
    "uk": ".co.uk",
    "au": ".co.au",
    "fr": ".fr",
    "de": ".de",
    "jp": ".co.jp",
    "it": ".it",
    "in": ".co.in",
    "es": ".es"
}

AUDIBLE_URL_BASE = "https://www.audible"
COUNTRY_CODE = "uk"

help_dict = {
    "download_books": "Downloads all books"
}


class ExternalError:

    def __init__(self, initiator, asin, error):
        self.initiator = initiator
        self.asin = asin
        self.error = error

    def show_error(self):
        print(
            f"Error while executing {self.initiator}, for ASIN: {self.asin}, msg: {self.error}")


class AudibleAPI:

    def __init__(self, auth):
        self.auth = auth
        self.books = []
        self.book_details = []
        self.library = {}

    async def welcome(self):
        print("Audible Bookmark Extractor v1.0")
        print("To authenticate with Audible, enter authenticate_now")

    async def cmd_get_book_infos(self, asin):
        async with audible.AsyncClient(self.auth) as client:
            try:
                book = await client.get(
                    path=f"library/{asin}",
                    params={
                        "response_groups": (
                            "contributors, media, price, reviews, product_attrs, "
                            "product_extended_attrs, product_desc, product_plan_details, "
                            "product_plans, rating, sample, sku, series, ws4v, origin, "
                            "relationships, review_attrs, categories, badge_types, "
                            "category_ladders, claim_code_url, is_downloaded, pdf_url, "
                            "is_returnable, origin_asin, percent_complete, provided_review"
                        )
                    }
                )
                return book
            except Exception as e:
                print(e)

    async def main(self):
        print("To download your audiobooks, ensure you are authenticated, then enter download_books")
        await self.enter_command()

    # TODO add authentication
    async def enter_command(self):
        command_input = input("Enter command: ")
        command = command_input.split(" ")[0]
        additional_kwargs = command_input.replace(command, '')
        _kwargs = {}
        if additional_kwargs:

            for kwarg in additional_kwargs.split(" --"):
                if kwarg == "":
                    continue
                li_kwarg = kwarg.split("=")

                if not len(li_kwarg) > 1:
                    await self.invalid_kwarg_callback()

                _kwargs[li_kwarg[0]] = li_kwarg[1]

        await getattr(self, f"cmd_{command}", self.invalid_command_callback)(**_kwargs)

        # except (AttributeError, TypeError):
        # return await self.invalid_kwarg_callback()

    async def invalid_command_callback(self):
        print("Invalid command, try again")
        await self.enter_command()

    async def invalid_kwarg_callback(self):
        print("Invalid command or arguments supplied, try again")
        await self.enter_command()

    async def get_book_selection(self, library):
        asins = []
        for index, book in enumerate(library["items"]):
            asins.append(book["asin"])
            book_title = book.get("title", "Unable to retrieve book name")
            print(f"{index}: {book_title}")

        book_selection = input(
            "Enter the index number of the book you would like to download, or enter --all for all available books: \n")

        if book_selection == "--all":
            asins = [book["asin"] for book in library["items"]]

        else:
            try:
                asins = [library["items"]
                         [int(book_selection)].get("asin", None)]
            except (IndexError, ValueError):
                print("Invalid selection")
                await self.invalid_command_callback()
        return asins

    async def cmd_download_books_entire(self):
        async with audible.AsyncClient(self.auth) as client:

            library = await client.get(
                path="library",
                params={
                    "num_results": 999
                }
            )

            asins = await self.get_book_selection(library)

            tasks = []
            for asin in asins:
                tasks.append(asyncio.ensure_future(
                    self.cmd_get_book_infos(asin)))

            books = await asyncio.gather(*tasks)

            all_books = {}

            for book in books:
                if book is not None:

                    print(book["item"]["title"])
                    asin = book["item"]["asin"]
                    raw_title = book["item"]["title"]
                    title = raw_title.replace(" ", "_")
                    all_books[asin] = title

                    try:
                        re = self.get_download_url(self.generate_url(
                            COUNTRY_CODE, "download", asin), num_results=1000, response_groups="product_desc, product_attrs")
                    except audible.exceptions.NetworkError as e:
                        ExternalError(self.get_download_url,
                                      asin, e).show_error()
                        continue

                    audible_response = requests.get(re, stream=True)
                    if audible_response.ok:
                        with open(f'audiobooks/{title}.aax', 'wb') as f:
                            print("Downloading %s" % raw_title)

                            total_length = audible_response.headers.get(
                                'content-length')

                            if total_length is None:  # no content length header
                                print(
                                    "Unable to estimate download size, downloading, this might take a while...")
                                f.write(audible_response.content)
                            else:
                                dl = 0
                                total_length = int(total_length)
                                for data in audible_response.iter_content(chunk_size=4096):
                                    dl += len(data)
                                    f.write(data)
                                    done = int(50 * dl / total_length)
                                    sys.stdout.write("\r[%s%s]" % (
                                        '=' * done, ' ' * (50-done)))

                                    sys.stdout.write(
                                        f"   {int(dl / total_length * 100)}%")
                                    sys.stdout.flush()
                                await self.main()
                                # f.write(audible_response.content)
                                # TODO add return to previous prompt

                    else:
                        # TODO add return to previous prompt
                        print(audible_response.text)
                        await self.main()

    def generate_url(self, country_code, url_type, asin=None):
        if asin and url_type == "download":
            return f"{AUDIBLE_URL_BASE}{country_code_mapping.get(country_code)}/library/download?asin={asin}&codec=AAX_44_128"

    def get_download_link_callback(self, resp):
        return resp.next_request

    def get_download_url(self, url, **kwargs):

        with audible.Client(auth=self.auth, response_callback=self.get_download_link_callback) as client:
            library = client.get(
                url,
                **kwargs
            )
            return library.url

    async def cmd_list_books(self):
        if not self.books:
            await self.cmd_get_library()

        self.cmd_show_library()

        await self.main()

    async def cmd_help(self):
        for key in help_dict:
            print(f"{key} -- {help_dict[key]}")
        # print(help_dict)
        await self.main()

    async def cmd_get_library(self):
        async with audible.AsyncClient(self.auth) as client:

            self.library = await client.get(
                path="library",
                params={
                    "num_results": 999
                }
            )
            asins = [book["asin"] for book in self.library["items"]]

            # books = await asyncio.gather(*(dl_book(asin) for asin in asins))
            tasks = []
            for index, book in enumerate(self.library["items"]):
                asins.append(book["asin"])
                book_title = book.get("title", "Unable to retrieve book name")
                # print(f"{index}: {book_title}")
                self.books.append(book_title)

    async def cmd_show_library(self):
        for index, book in enumerate(self.books):
            book_title = book.get("title", "Unable to retrieve book name")
            print(f"{index}: {book_title}")

    async def cmd_download_books(self):
        all_books = {}

        if not self.books:
            await self.cmd_get_library()

        for book in self.books:
            if book is not None:
                breakpoint()
                print(book["item"]["title"])
                asin = book["item"]["asin"]
                raw_title = book["item"]["title"]
                title = raw_title.replace(" ", "_")
                all_books[asin] = title

                try:
                    re = self.get_download_url(self.generate_url(
                        COUNTRY_CODE, "download", asin), num_results=1000, response_groups="product_desc, product_attrs")
                except audible.exceptions.NetworkError as e:
                    ExternalError(self.get_download_url,
                                  asin, e).show_error()
                    continue

                audible_response = requests.get(re, stream=True)
                if audible_response.ok:
                    with open(f'{title}.aax', 'wb') as f:
                        print("Downloading %s" % raw_title)

                        total_length = audible_response.headers.get(
                            'content-length')

                        if total_length is None:  # no content length header
                            f.write(audible_response.content)
                        else:
                            dl = 0
                            total_length = int(total_length)
                            print(total_length)
                            for data in audible_response.iter_content(chunk_size=4096):
                                dl += len(data)
                                f.write(data)
                                done = int(50 * dl / total_length)
                                sys.stdout.write("\r[%s%s]" % (
                                    '=' * done, ' ' * (50-done)))

                                sys.stdout.write(
                                    f"   {int(dl / total_length * 100)}%")
                                sys.stdout.flush()

                        f.write(audible_response.content)

                else:
                    print(audible_response.text)

    async def cmd_get_bookmarks(self):
        if not self.library:
            self.cmd_get_library()

        await self.get_book_selection(self.library)

    def get_bookmarks(self, asin):
        bookmarks_url = f"https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/sidecar?type=AUDI&key={asin}"
        with audible.Client(auth=self.auth, response_callback=self.bookmark_response_callback) as client:
            library = client.get(
                bookmarks_url,
                num_results=1000,
                response_groups="product_desc, product_attrs"
            )
            return library.json()

    def bookmark_response_callback(resp):
        return resp


if __name__ == "__main__":
    # authenticate with login
    auth = audible.Authenticator.from_file("credentials.json")

    loop = asyncio.get_event_loop()

    audible_obj = AudibleAPI(auth)
    loop.run_until_complete(audible_obj.welcome())
    loop.run_until_complete(audible_obj.main())
