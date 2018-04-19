# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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
import os

import pytest
import shutil


@pytest.fixture(scope='module')
def input_files(tmpdir_factory, request):
    tmpdir = tmpdir_factory.mktemp('data')
    samples_dir = os.path.dirname(str(
        request.fspath)) + "/" + "../yaml_samples"
    samples = os.listdir(samples_dir)

    for f in samples:
        src_file = samples_dir + "/" + f
        dst_file = str(tmpdir) + "/" + f
        shutil.copyfile(src_file, dst_file)
    return tmpdir
