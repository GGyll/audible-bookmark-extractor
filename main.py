from urllib import response
import audible
import requests
from pydub import AudioSegment

auth = audible.Authenticator.from_file("credentials.json")

bookmarks_url = "https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/sidecar?type=AUDI&key=1473565421"

content_url = "/1.0/content/1473565421/licenserequest"


def bookmark_response_callback(resp):
    return resp


def get(url, **kwargs):

    with audible.Client(auth=auth, response_callback=bookmark_response_callback) as client:
        library = client.get(
            url,
            **kwargs
        )
        print(library)
        return library.json()


# bookmarks_dict = get(bookmarks_url, num_results=1000,
#                      response_groups="product_desc, product_attrs")

# li_clips = bookmarks_dict.get("payload").get("records")
# audio_book = AudioSegment.from_wav("file_name.wav")

# file_counter = 1
# for audio_clip in li_clips:
#     if audio_clip.get("type", None) == "audible.clip":
#         start_pos = int(audio_clip["startPosition"]) - 3000
#         end_pos = int(audio_clip["endPosition"])
#         clip = audio_book[start_pos:end_pos]
#         try:
#             note = audio_clip.get("metadata", None).get("note")
#             file_name = note
#         except AttributeError:
#             file_name = f"clip{file_counter}"
#         clip.export(f"clips/{file_name}.flac", format="flac")
#         file_counter += 1


# {"paylod": {"records": [{"creationTime", "type": "audible.clip", "startPosition", "endPosition", "metadata": {"note": "Aggregatopm"}}]}}
request_body = {
    "supported_drm_types": [
        "Mpeg",
        "Adrm"
    ],
    "quality": "Normal",
    "consumption_type": "Download",
    "response_groups": "last_position_heard,pdf_url,content_reference,chapter_info"
}


def post(url, **kwargs):

    with audible.Client(auth=auth) as client:
        library = client.post(
            url,
            request_body
        )
        return library["content_license"]["content_metadata"]["content_url"]["offline_url"]


# print(post(content_url))
download_url = post(content_url)

response = requests.get(download_url)

open("test.aax", "wb").write(response.content)
