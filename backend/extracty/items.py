class UGGPlayerResponse(dict):
    pass


class UGGMatchResponse(dict):
    pass


class UGGMatchDetailResponse(dict):
    pass


class AssetItem(dict):
    """An image to store at `keys` (e.g. `["item/3158.png"]`, several when ids
    share an image), see `AssetFilesPipeline`.

    `file_urls` (a single source URL) and `files` are `FilesPipeline` fields.
    """
