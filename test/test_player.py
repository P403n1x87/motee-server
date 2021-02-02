from motee.message import Request

from test import start_server_and_send_request as sssr


def test_player():
    response = sssr(Request(scope="player", action="list"))
    print(response.data)
    assert isinstance(response.data, dict)
