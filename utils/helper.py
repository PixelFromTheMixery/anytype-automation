def make_deeplink(space_id: str, object_id: str, internal: bool = True):
    """Builds deeplinks for link purposes"""
    if internal:
        return f"anytype://object?objectId={object_id}&spaceId={space_id}"
    return f"https://object.any.coop/{object_id}?spaceId={space_id}"
