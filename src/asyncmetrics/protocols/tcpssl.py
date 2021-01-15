from asyncio import StreamWriter, open_connection
from ssl import create_default_context

from .tcp import Tcp

__all__ = [
    'TcpSsl',
]


# TODO Test ssl
# noinspection PyAbstractClass
class TcpSsl(Tcp):
    def __init__(self, *args, ssl_crt=None, ssl_key=None, ssl_password=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._ssl_crt = ssl_crt
        self._ssl_key = ssl_key
        self._ssl_password = ssl_password

    async def _connect(self) -> StreamWriter:
        context = create_default_context()

        if self._ssl_crt:
            context.load_cert_chain(self._ssl_crt, self._ssl_key, self._ssl_password)

        _, writer = await open_connection(self._host, self._port, ssl=context)
        return writer
