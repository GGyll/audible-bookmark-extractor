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


class ExternalError:

    def __init__(self, initiator, asin, error):
        self.initiator = initiator
        self.asin = asin
        self.error = error

    def show_error(self):
        print(
            f"Error while executing {self.initiator}, for ASIN: {self.asin}, msg: {self.error}")


# ASYNC FUNCTIONS
async def get_book_infos(client, asin):
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


async def main(auth):
    async with audible.AsyncClient(auth) as client:
        print(repr(client))

        library = await client.get(
            path="library",
            params={
                "num_results": 999
            }
        )
        asins = [book["asin"] for book in library["items"]]

        # books = await asyncio.gather(*(dl_book(asin) for asin in asins))
        tasks = []
        for asin in asins:
            tasks.append(asyncio.ensure_future(get_book_infos(client, asin)))
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
                    re = get_download_url(generate_url(
                        COUNTRY_CODE, "download", asin), num_results=1000, response_groups="product_desc, product_attrs")
                except audible.exceptions.NetworkError as e:
                    ExternalError(get_download_url, asin, e).show_error()
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


def generate_url(country_code, url_type, asin=None):
    if asin and url_type == "download":
        return f"{AUDIBLE_URL_BASE}{country_code_mapping.get(country_code)}/library/download?asin={asin}&codec=AAX_44_128"


def get_download_link_callback(resp):
    return resp.next_request


def get_download_url(url, **kwargs):
    with audible.Client(auth=auth, response_callback=get_download_link_callback) as client:
        library = client.get(
            url,
            **kwargs
        )
        return library.url


if __name__ == "__main__":
    # authenticate with login
    # don't stores any credentials on your system
    auth = audible.Authenticator.from_file("credentials.json")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(auth))
