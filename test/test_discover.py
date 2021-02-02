from motee.message import Request

from test import start_server_and_send_request as sssr, get_connected_nic as nic


def test_player():
    response = sssr(Request(scope="discover"))
    assert response.data["inet"] == nic().ip
