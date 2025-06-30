# SPDX-License-Identifier: BSD-2-Clause

import os

# HACK(aki): Try to prevent Torii from automatically setting up the warning handler
os.environ['TORII_WARNINGS_NOHANDLE'] = '1'
