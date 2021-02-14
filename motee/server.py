import asyncio
from logging import basicConfig, getLogger, DEBUG

from motee.message import Response, Request
from motee.net import get_address
from motee.scope.app import AppHandler
from motee.scope.device import DeviceHandler
from motee.scope.player import PlayerHandler


LOGGER = getLogger(__name__)
basicConfig(level=DEBUG)

HANDLERS = {
    "app": AppHandler,
    "device": DeviceHandler,
    "player": PlayerHandler,
}


async def client_handler(reader, writer):
    client_name = writer.get_extra_info("peername")
    LOGGER.debug(f"Client {client_name} connected")
    try:
        while True:
            data = (await reader.readline()).strip().decode()
            if not data:
                writer.close()
                break
            request = Request.parse(data)
            LOGGER.debug(f"Received {request} from client {client_name}")
            handler = HANDLERS.get(request.scope, None)
            if handler is None:
                raise RuntimeError(f"Unknown scope: {request.scope}")
            response_data = handler.handle(request.action, request.data)
            if response_data is not None:
                response = (
                    response_data is True
                    and Response.ok(request)
                    or Response(
                        scope=request.scope,
                        correlation=request.id,
                        content=request.action,
                        data=response_data,
                    )
                )
                LOGGER.debug(f"Sending {response} to client {client_name}")
                writer.write(response.encode())
            await writer.drain()
    except ConnectionResetError:
        pass
    except Exception as e:
        LOGGER.error(e, exc_info=e)
        raise e


def serve(host="localhost", port=8787):
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(
        asyncio.start_server(client_handler, host=host, port=port)
    )
    try:
        loop.run_until_complete(server.serve_forever()).result()
    finally:
        server.close()


def main():
    ip = get_address()
    LOGGER.info(f"Serving on {ip}:8787")
    serve(host=ip)


if __name__ == "__main__":
    main()
