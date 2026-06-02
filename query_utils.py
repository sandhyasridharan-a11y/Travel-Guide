from urllib.parse import unquote_plus


def build_page_query_params(page, focus=None):
    params = {"page": [page]}
    if page == "guidance" and focus:
        params["focus"] = [focus]
    return params


def sync_page_query_params(page, focus=None):
    return build_page_query_params(page, focus)


def resolve_section_page(query_page, current_session_page=None):
    valid_options = ["Overview", "Itinerary", "Guidance"]
    normalized = query_page.capitalize() if query_page else "Overview"
    selected = normalized if normalized in valid_options else "Overview"
    if current_session_page != selected:
        return selected
    return current_session_page


def normalize_focus_param(focus):
    if focus is None:
        return None
    return unquote_plus(focus)
