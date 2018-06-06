# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""String redaction based upon regex patterns

Uses the keys and patterns from oslo_utils as a starting point, and layers in
new keys and patterns defined locally.
"""
import re

# oslo_utils makes the choice to keep the list of supported redactions
# non-extensible (purposefully). Here we can define new values, and follow the
# same basic logic as used in strutils.
# The following are copied from oslo_utils, strutils. Extend using the other
# facilties to make these easier to keep in sync:
_FORMAT_PATTERNS_1 = [r'(%(key)s\s*[=]\s*)[^\s^\'^\"]+']
_FORMAT_PATTERNS_2 = [r'(%(key)s\s*[=]\s*[\"\'])[^\"\']*([\"\'])',
                      r'(%(key)s\s+[\"\'])[^\"\']*([\"\'])',
                      r'([-]{2}%(key)s\s+)[^\'^\"^=^\s]+([\s]*)',
                      r'(<%(key)s>)[^<]*(</%(key)s>)',
                      r'([\"\']%(key)s[\"\']\s*:\s*[\"\'])[^\"\']*([\"\'])',
                      r'([\'"][^"\']*%(key)s[\'"]\s*:\s*u?[\'"])[^\"\']*'
                      '([\'"])',
                      r'([\'"][^\'"]*%(key)s[\'"]\s*,\s*\'--?[A-z]+\'\s*,\s*u?'
                      '[\'"])[^\"\']*([\'"])',
                      r'(%(key)s\s*--?[A-z]+\s*)\S+(\s*)']
_SANITIZE_KEYS = ['adminPass', 'admin_pass', 'password', 'admin_password',
                  'auth_token', 'new_pass', 'auth_password', 'secret_uuid',
                  'secret', 'sys_pswd', 'token', 'configdrive',
                  'CHAPPASSWORD', 'encrypted_key']


class Redactor():
    """String redactor that can be used to replace sensitive values

    :param redaction: the string value to put in place in case of a redaction
    :param keys: list of additional keys that are searched for and have related
        values redacted
    :param single_patterns: list of additional single capture group regex
        patterns
    :param double_patterns: list of additional double capture group regex
        patterns
    """
    # Start with the values defined in strutils
    _KEYS = list(_SANITIZE_KEYS)

    _SINGLE_CG_PATTERNS = list(_FORMAT_PATTERNS_1)
    _DOUBLE_CG_PATTERNS = list(_FORMAT_PATTERNS_2)

    # More keys to extend the set of keys used in identifying redactions
    _KEYS.extend([])
    # More single capture group patterns
    _SINGLE_CG_PATTERNS.extend([r'(%(key)s\s*[:]\s*)[^\s^\'^\"]+'])
    # More two capture group patterns
    _DOUBLE_CG_PATTERNS.extend([])

    def __init__(self,
                 redaction='***',
                 keys=None,
                 single_patterns=None,
                 double_patterns=None):
        if keys is None:
            keys = []
        if single_patterns is None:
            single_patterns = []
        if double_patterns is None:
            double_patterns = []

        self.redaction = redaction

        self.keys = list(Redactor._KEYS)
        self.keys.extend(keys)

        singles = list(Redactor._SINGLE_CG_PATTERNS)
        singles.extend(single_patterns)

        doubles = list(Redactor._DOUBLE_CG_PATTERNS)
        doubles.extend(double_patterns)

        self._single_cg_patterns = self._gen_patterns(patterns=singles)
        self._double_cg_patterns = self._gen_patterns(patterns=doubles)
        # the two capture group patterns

    def _gen_patterns(self, patterns):
        """Initialize the redaction patterns"""
        regex_patterns = {}
        for key in self.keys:
            regex_patterns[key] = []
            for pattern in patterns:
                reg_ex = re.compile(pattern % {'key': key}, re.DOTALL)
                regex_patterns[key].append(reg_ex)
        return regex_patterns

    def redact(self, message):
        """Apply regex based replacements to mask values

        Modeled from:
        https://github.com/openstack/oslo.utils/blob/9b23c17a6be6d07d171b64ada3629c3680598f7b/oslo_utils/strutils.py#L272
        """
        substitute1 = r'\g<1>' + self.redaction
        substitute2 = r'\g<1>' + self.redaction + r'\g<2>'

        for key in self.keys:
            if key in message:
                for pattern in self._double_cg_patterns[key]:
                    message = re.sub(pattern, substitute2, message)
                for pattern in self._single_cg_patterns[key]:
                    message = re.sub(pattern, substitute1, message)
        return message
