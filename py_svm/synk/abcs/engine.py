# Standard Library
import abc
import json
from typing import Any, Dict, Optional

import httpx
from loguru import logger as log
from pydantic import BaseModel
import inspect
import devtools
import orjson


class AbstractEngine(abc.ABC):
    """This is where the database is supposed to interact with the client."""

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        """Connects to the database."""
        raise NotImplementedError

    def disconnect(self):
        """Disconnects from the database."""
        raise NotImplementedError

    def execute(self, query: str, params: Optional[dict] = None) -> dict:
        return {}

    def query(self, query: str, params: Optional[dict] = None) -> dict:
        return {}

    def reset(self):
        raise NotImplementedError


class HeadersBuilder(BaseModel, abc.ABC):
    content_type: str = 'application/json'

    def get_default_headers(self) -> dict:
        return {
            'Content-Type': self.content_type,
        }


class AuthProvider:

    def basic(self, username: str, password: str) -> httpx.Auth:
        return httpx.BasicAuth(username, password)

    def token(self, token: str) -> httpx.Auth:
        raise NotImplementedError
        # self.auth_type = auth_type
        # self.auth_data = auth_data

    def get_auth_header(self) -> dict:
        return {}


def log_request(request: httpx.Request):
    devtools.debug(request.headers)
    # log.warning(
    #     f"Request event hook: {request.method} {request.url}  - Waiting for response"
    # )


def log_response(response: httpx.Response):
    request = response.request
    log.info(
        f"Response event hook: {request.method} {request.url} - Status {response.status_code}"
    )
    devtools.debug({
        "headers": dict(response.headers),
        "body": orjson.loads(response.read())
    })


class HTTPEngine(AbstractEngine):
    """This is where the database is supposed to interact with the client."""

    def __init__(
            self,
            url: str,
            username: str | None = None,
            password: str | None = None,
            default_headers: HeadersBuilder = HeadersBuilder(),
    ):
        self.url = url.strip('/')
        self.auth = None
        self.provider = AuthProvider()
        self.username = username
        self.password = password
        if self.username and self.password:
            self.auth = self.provider.basic(self.username, self.password)
        self.headers_builder = default_headers
        self._session: httpx.Client | None = None
        self.reset()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)

    @property
    def session(self) -> httpx.Client:
        """The session property."""
        if self._session is None:
            raise ValueError("Session is not initialized")
        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    @property
    def is_auth(self) -> bool:
        return self.auth is not None

    def connect(self):
        """Connects to the database."""
        if not self._session:
            self.reset()
        log.success("Faking a connection to the database.")

    def disconnect(self):
        """Disconnects from the database."""
        log.error("Disconnecting")

    def execute(self, query: str, params: Optional[dict] = None) -> dict:
        """
        `execute` executes a query
        
        :param query: The query to execute
        :type query: str
        :param params: Optional[dict] = None
        :type params: Optional[dict]
        :return: A dictionary.
        """
        raise NotImplementedError("Execute is not implemented")
        # log.warning("Executing query: {}", query)
        # return {}

    def request(self, method: str, path: str, **kwargs):
        return self.session.request(method, path, **kwargs)

    def reset(self):
        _auth = dict(auth=self.auth) if self.auth else {}
        _headers = self.headers_builder.get_default_headers()
        self.session = httpx.Client(
            base_url=self.url,
            headers=_headers,
            event_hooks={
                'request': [log_request],
                'response': [log_response]
            },
            **_auth,
        )

        return self.session

    def get(
            self,
            path: str,
            params: dict | None = None,
            headers: dict | None = None,
            cookies: httpx.Cookies | None = None,
            follow_redirects: bool = False,
            timeout=httpx.Timeout(timeout=5.0),
    ):
        return self.session.get(
            f"{path.strip('/')}",
            params=params,
            headers=headers,
            cookies=cookies,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    def post(
        self,
        path: str,
        content: bytes | None = None,
        data: Dict[str, Any] | None = None,
        files=None,
        json: Dict[str, Any] | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
        timeout=httpx.Timeout(timeout=5.0),
        follow_redirects: bool = False,
    ) -> httpx.Response:
        return self.session.post(
            f"/{path.strip('/')}",
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(url={self.url}, auth={self.is_auth}, username={self.username}, password={'*' * min(len(self.password)*5, 9)})"  # type: ignore


def main():

    class SurrealHeaders(HeadersBuilder):
        ns: str = 'test'
        db: str = 'test'

        def get_default_headers(self) -> dict:
            return {
                'Content-Type': 'application/json',
                'NS': self.ns,
                'DB': self.db,
            }

    class SurrealEngine(HTTPEngine):

        def execute(self, query: str, params: Optional[dict] = None) -> dict:
            with log.catch(onerror=log.error,
                           message="Error executing query",
                           default=dict()):
                return self.post('/sql', data=query)  # type: ignore

    http_engine = SurrealEngine("http://0.0.0.0:8000",
                                "root",
                                "root",
                                default_headers=SurrealHeaders())

    with http_engine as engine:
        engine.execute("SELECT * FROM author, article, account;")
        engine.execute("INFO FOR DB;")
    import devtools
    # devtools.debug(inspect.signature(http_engine.session.post))

    # http_engine.connect()
    log.debug(http_engine)
    print("hello world")


if __name__ == "__main__":
    main()
