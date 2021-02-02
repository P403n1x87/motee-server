import asyncio
from base64 import b64encode
from logging import basicConfig, getLogger, DEBUG

from motee.apps import active_app, app, apps
from motee.device import Device
from motee.media import players, get_player
from motee.message import Response, Request
from motee.net import hostname, nics


LOGGER = getLogger(__name__)
basicConfig(level=DEBUG)


class Handlers:
    @staticmethod
    def handle_app(request, writer):
        if request.action == "list":
            return Response(
                scope="app",
                content="list",
                correlation=request.id,
                data={
                    _.name: {"wid": _.wid, "icon": b64encode(_.icon or b"").decode()}
                    for _ in apps()
                    # if _.icon is not None
                },
            )
        elif request.action == "activate":
            wid = request.data["wid"]
            aapp = active_app()
            if aapp.wid == wid:
                aapp.toggle_fullscreen()
            else:
                app(request.data["wid"]).activate()
            return Response.ok(request)
        elif request.action == "close":
            active_app().close()
            return Response.ok(request)

    @staticmethod
    def handle_device(request, writer):
        if request.action == "volume":
            getattr(Device(), f"volume_{request.data['direction']}")()
        elif request.action == "cursor":
            Device().move_cursor(request.data["dx"], request.data["dy"])
        elif request.action == "poweroff":
            Device().shutdown()
        elif request.action == "reboot":
            Device().reboot()
        elif request.action == "launch":
            Device().launch(request.data["command"])
        return Response.ok(request)

    @staticmethod
    def handle_player(request, writer):
        action = request.action
        if action == "list":
            return Response(
                scope="player",
                content="list",
                correlation=request.id,
                data={
                    _.name: {"status": _.status, "metadata": _.metadata}
                    for _ in players()
                },
            )

        elif action == "play_pause":
            try:
                player = get_player(request.data["name"])
                player.play_pause()
                return Response(
                    scope="player",
                    content="info",
                    correlation=request.id,
                    data={"result": "OK"},
                )
            except Exception as e:
                return Response(
                    scope="player",
                    content="error",
                    correlation=request.id,
                    data={"details": str(e)},
                )

    @staticmethod
    def handle_discover(request, writer):
        inet, port = writer.get_extra_info("sockname")
        mac = {n.ip: n.mac for n in nics() if n.connected}.get(inet, None)
        return (
            Response(
                correlation=request.id,
                scope="discover",
                content="info",
                data={"host": hostname(), "inet": inet, "port": port, "mac": mac},
            )
            if mac
            else Response(
                correlation=request.id,
                scope="discover",
                content="error",
                data="no MAC address for host",
            )
        )


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
            handler = getattr(Handlers, f"handle_{request.scope}", None)
            if handler is None:
                raise RuntimeError(f"Unknown scope: {request.scope}")
            response = handler(request, writer)
            if isinstance(response, Response):
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


if __name__ == "__main__":
    for nic in nics():
        if nic.connected:
            ip = nic.ip
            break
        else:
            ip = "localhost"
    LOGGER.info(f"Serving on {ip}:8787")
    serve(host=ip)
