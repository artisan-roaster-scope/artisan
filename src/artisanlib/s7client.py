#

import snap7.client

# patch S7 client


class S7Client(snap7.client.Client):
    def __init__(self) -> None:
        super().__init__()

    # avoiding an exception on __del__ as self.library might not yet be set if loading of shared lib failed!
    def destroy(self) -> None:
        if hasattr(self, 'library'):
            super().destroy()
