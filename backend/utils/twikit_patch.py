# MONKEY PATCH:
import re

_tx_mod = __import__('twikit.x_client_transaction.transaction', fromlist=['ClientTransaction'])

_tx_mod.ON_DEMAND_FILE_REGEX = re.compile(
    r""",(\d+):["']ondemand\.s["']""", flags=(re.VERBOSE | re.MULTILINE)
)
_tx_mod.ON_DEMAND_HASH_PATTERN = r',{}:"([0-9a-f]+)"'

async def _patched_get_indices(self, home_page_response, session, headers):
    key_byte_indices = []
    response = self.validate_response(home_page_response) or self.home_page_response
    on_demand_file_index = _tx_mod.ON_DEMAND_FILE_REGEX.search(str(response)).group(1)
    regex = re.compile(_tx_mod.ON_DEMAND_HASH_PATTERN.format(on_demand_file_index))
    filename = regex.search(str(response)).group(1)
    on_demand_file_url = f"https://abs.twimg.com/responsive-web/client-web/ondemand.s.{filename}a.js"
    on_demand_file_response = await session.request(method="GET", url=on_demand_file_url, headers=headers)
    key_byte_indices_match = _tx_mod.INDICES_REGEX.finditer(str(on_demand_file_response.text))
    for item in key_byte_indices_match:
        key_byte_indices.append(item.group(2))
    if not key_byte_indices:
        raise Exception("Couldn't get KEY_BYTE indices")
    key_byte_indices = list(map(int, key_byte_indices))
    return key_byte_indices[0], key_byte_indices[1:]

_tx_mod.ClientTransaction.get_indices = _patched_get_indices
# END MONKEY PATCH

# MONKEY PATCH: backfill missing keys X's API sometimes omits from user payloads
import twikit.user as _user_mod

_original_user_init = _user_mod.User.__init__

_LEGACY_DEFAULTS = {
    'created_at': '',
    'name': '',
    'screen_name': '',
    'profile_image_url_https': '',
    'location': '',
    'description': '',
    'verified': False,
    'possibly_sensitive': False,
    'can_dm': False,
    'can_media_tag': False,
    'want_retweets': False,
    'default_profile': False,
    'default_profile_image': False,
    'has_custom_timelines': False,
    'followers_count': 0,
    'fast_followers_count': 0,
    'normal_followers_count': 0,
    'friends_count': 0,
    'favourites_count': 0,
    'listed_count': 0,
    'media_count': 0,
    'statuses_count': 0,
    'is_translator': False,
    'translator_type': '',
    'withheld_in_countries': [],
    'pinned_tweet_ids_str': [],
}

def _patched_user_init(self, client, data):
    data.setdefault('rest_id', '')
    data.setdefault('is_blue_verified', False)

    legacy = data.setdefault('legacy', {})
    for key, default in _LEGACY_DEFAULTS.items():
        legacy.setdefault(key, default)

    entities = legacy.setdefault('entities', {})
    entities.setdefault('description', {}).setdefault('urls', [])

    _original_user_init(self, client, data)

_user_mod.User.__init__ = _patched_user_init
# END MONKEY PATCH