from . import constants



def _headers(anon_key: bool) -> dict:
    if anon_key:
        api_key = constants.ANON_KEY_BYTES.decode()
    else:
        api_key = constants.KEY_BYTES.decode()
    return {
        'Content-Type': 'application/json',
        'x-changenow-api-key': api_key,
    }


def headers(anon_key: bool):
    """
    Return the headers
    :param anon_key: use the alternate, anonymous key if true
    :return: dict
    """
    return _headers(anon_key)
