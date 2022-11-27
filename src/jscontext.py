from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Dict, List, Union

import dukpy

from src.cssparser import CSSParser
from src.network import request
from src.task import Task
from src.text import Element, HTMLParser
from src.util.node import tree_to_list
from src.util.url import resolve_url, url_origin

if TYPE_CHECKING:
    from src.graphics.tab import Tab

EVENT_DISPATCH_CODE: str = "new Node(dukpy.handle).dispatchEvent(new Event(dukpy.type))"
SETTIMEOUT_CODE = "__runSetTimeout(dukpy.handle)"
XHR_ONLOAD_CODE = "__runXHROnload(dukpy.out, dukpy.handle)"


class JSContext:
    def __init__(self, tab: Tab):
        self.tab = tab
        self.interp = dukpy.JSInterpreter()
        self.interp.export_function("log", print)
        self.interp.export_function("querySelectorAll", self.querySelectorAll)
        self.interp.export_function("getAttribute", self.getAttribute)
        self.interp.export_function("innerHTML_set", self.innerHTML_set)
        self.interp.export_function("XMLHttpRequest_send", self.XMLHttpRequest_send)
        self.interp.export_function("setTimeout", self.setTimeout)

        with open("src/runtime.js") as f:
            self.interp.evaljs(f.read())

        self.node_to_handle: Dict[Element, int] = {}
        self.handle_to_node: Dict[int, Element] = {}

    def run(self, code: str):
        return self.interp.evaljs(code)

    def innerHTML_set(self, handle: int, s: str):
        doc = HTMLParser("<html><body>" + s + "</body></html>").parse()
        new_nodes = doc.children[0].children

        elt = self.handle_to_node[handle]
        elt.children = new_nodes
        for child in elt.children:
            child.parent = elt
        self.tab.render()

    def dispatch_event(self, type: str, elt: Element) -> bool:
        handle = self.node_to_handle.get(elt, -1)
        do_default = self.interp.evaljs(EVENT_DISPATCH_CODE, type=type, handle=handle)
        return not do_default

    def get_handle(self, elt: Element) -> int:
        if elt not in self.node_to_handle:
            handle = len(self.node_to_handle)
            self.node_to_handle[elt] = handle
            self.handle_to_node[handle] = elt
        else:
            handle = self.node_to_handle[elt]
        return handle

    def querySelectorAll(self, selector_text: str) -> List[int]:
        selector = CSSParser(selector_text).selector()
        nodes: List[Element] = [
            node for node in tree_to_list(self.tab.nodes, []) if selector.matches(node)
        ]
        return [self.get_handle(node) for node in nodes]

    def getAttribute(self, handle: int, attr: str) -> Union[str, None]:
        elt = self.handle_to_node[handle]
        return elt.attributes.get(attr, None)

    def dispatch_xhr_onload(self, out, handle):
        _ = self.interp.evaljs(XHR_ONLOAD_CODE, out=out, handle=handle)

    def XMLHttpRequest_send(
        self, method: str, url: str, body: Union[str, None], isasync: bool, handle: int
    ):
        full_url = resolve_url(self.tab.url, url)
        assert full_url is not None
        if not self.tab.allowed_request(full_url):
            raise Exception("Cross-origin XHR blocked by CSP")
        if url_origin(full_url) != url_origin(self.tab.url):
            raise Exception("Cross-origin XHR request not allowed")

        def run_load():
            headers, response, _ = request(full_url, self.tab.url, payload=body)
            task = Task(self.dispatch_xhr_onload, response, handle)
            self.tab.task_runner.schedule_task(task)
            if not isasync:
                return response

        if not isasync:
            return run_load()
        else:
            threading.Thread(target=run_load).start()

    def dispatch_settimeout(self, handle: int):
        self.interp.evaljs(SETTIMEOUT_CODE, handle=handle)

    def setTimeout(self, handle: int, time: float):
        def run_callback():
            task = Task(self.dispatch_settimeout, handle)
            self.tab.task_runner.schedule_task(task)

        threading.Timer(time / 1000.0, run_callback).start()
