import asyncio

try:
    from functools import cache as cached
except ImportError:
    from functools import lru_cache

    cached = lru_cache()

from motee.message import Request, Response
from motee.net import nics
from motee.server import serve


@cached
def get_connected_nic():
    for nic in nics():
        if nic.connected:
            return nic
        else:
            raise RuntimeError("No connected NICs found")


def start_server_and_send_request(request: Request) -> Response:
    async def send_request(nic) -> Response:
        for i in range(10):
            try:
                reader, writer = await asyncio.open_connection(nic.ip, 8787)
                break
            except ConnectionRefusedError:
                await asyncio.sleep(0.1)

        try:
            writer.write(request.encode())
            return Response.parse((await reader.readline()).decode())
        finally:
            writer.close()
            loop.stop()

    nic = get_connected_nic()

    loop = asyncio.get_event_loop()
    task = loop.create_task(send_request(nic))

    try:
        serve(host=nic.ip)
    except RuntimeError:
        pass

    return task.result()
