from __future__ import annotations

from urllib.parse import urlencode

PAGE_TITLES = {
    "/timer": "Timer",
    "/aufnahmen": "Aufnahmen",
    "/sender": "Sender",
    "/epg": "EPG",
    "/timer/new": "Timer erstellen",
    "/timer/edit": "Timer bearbeiten",
}


def loading_response(request, *, render, selected_receiver, can_write_receiver):
    path = request.url.path
    if request.method != "GET" or path not in PAGE_TITLES:
        return None
    receiver = selected_receiver(request)
    if request.headers.get("X-Receiver-Data") == "1":
        if not receiver or request.headers.get("X-Receiver-Id") != str(receiver.id):
            response = render(
                request,
                "error.html",
                status=409,
                code=409,
                error="Der Receiver wurde gewechselt. Bitte die Seite neu öffnen.",
            )
            response.headers["X-Receiver-Changed"] = "1"
            return response
        return None
    if (
        not receiver
        or "text/html" not in request.headers.get("accept", "")
        or request.headers.get("X-Live-Refresh")
        or request.query_params.get("load") == "direct"
        or (path == "/epg" and not request.query_params.get("reference"))
    ):
        return None
    if path in {"/timer/new", "/timer/edit"} and not can_write_receiver(request, receiver):
        return render(
            request,
            "error.html",
            status=403,
            code=403,
            error="Für diesen Receiver sind nur Leserechte vergeben.",
        )
    query = [(key, value) for key, value in request.query_params.multi_items() if key != "load"]
    direct_url = path + "?" + urlencode([*query, ("load", "direct")])
    return render(
        request,
        "loading.html",
        page_title=PAGE_TITLES[path],
        show_selection=path not in {"/timer/new", "/timer/edit"},
        direct_url=direct_url,
    )
