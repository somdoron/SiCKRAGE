

# Authors: Mr_Orange <mr_orange@hotmail.it>, EchelonFour
# URL: https://sickrage.ca
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

import sickrage
from sickrage.clients import GenericClient


class uTorrentAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(uTorrentAPI, self).__init__('uTorrent', host, username, password)

        self.url = self.host + 'gui/'

    def _request(self, method='get', data=None, params=None, *args, **kwargs):

        # Workaround for uTorrent 2.2.1
        # Need a odict but only supported in 2.7+ and sickrage is 2.6+
        ordered_params = {'token': self.auth}

        for k, v in params.items() or {}:
            ordered_params.update({k: v})

        return super(uTorrentAPI, self)._request(method=method, params=ordered_params, data=data, *args, **kwargs)

    def _get_auth(self):

        try:
            self.response = sickrage.srCore.srWebSession.get(self.url + 'token.html',
                                                             timeout=120,
                                                             auth=(self.username, self.password),
                                                             verify=bool(sickrage.srCore.srConfig.TORRENT_VERIFY_CERT))

            self.auth = re.findall("<div.*?>(.*?)</", self.response.text)[0]
            self.cookies = self.response.cookies
        except Exception:
            return None

        return self.auth if not self.response.status_code == 404 else None

    def _add_torrent_uri(self, result):

        params = {'action': 'add-url', 's': result.url}
        return self._request(params=params)

    def _add_torrent_file(self, result):

        params = {'action': 'add-file'}
        files = {'torrent_file': (result.name + '.torrent', result.content)}
        return self._request(method='post', params=params, files=files)

    def _set_torrent_label(self, result):

        label = sickrage.srCore.srConfig.TORRENT_LABEL
        if result.show.is_anime:
            label = sickrage.srCore.srConfig.TORRENT_LABEL_ANIME

        params = {'action': 'setprops',
                  'hash': result.hash,
                  's': 'label',
                  'v': label}

        return self._request(params=params)

    def _set_torrent_ratio(self, result):

        ratio = None
        if result.ratio:
            ratio = result.ratio

        if ratio:
            params = {'action': 'setprops',
                      'hash': result.hash,
                      's': 'seed_override',
                      'v': '1'}

            if self._request(params=params):
                params = {'action': 'setprops',
                          'hash': result.hash,
                          's': 'seed_ratio',
                          'v': float(ratio) * 10}

                return self._request(params=params)
            else:
                return False

        return True

    def _set_torrent_seed_time(self, result):

        if sickrage.srCore.srConfig.TORRENT_SEED_TIME:
            time = 3600 * float(sickrage.srCore.srConfig.TORRENT_SEED_TIME)
            params = {'action': 'setprops',
                      'hash': result.hash,
                      's': 'seed_override',
                      'v': '1'}

            if self._request(params=params):
                params = {'action': 'setprops',
                          'hash': result.hash,
                          's': 'seed_time',
                          'v': time}

                return self._request(params=params)
            else:
                return False
        else:
            return True

    def _set_torrent_priority(self, result):

        if result.priority == 1:
            params = {'action': 'queuetop', 'hash': result.hash}
            return self._request(params=params)
        else:
            return True

    def _set_torrent_pause(self, result):

        if sickrage.srCore.srConfig.TORRENT_PAUSED:
            params = {'action': 'pause', 'hash': result.hash}
        else:
            params = {'action': 'start', 'hash': result.hash}

        return self._request(params=params)


api = uTorrentAPI()
