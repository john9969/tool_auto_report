import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class API:
    def __init__(self, api_url: str, headers: dict | None = None, timeout: float = 15.0):
        self.api_url = api_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; WaterBot/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        if headers:
            self.headers.update(headers)
        self.timeout = timeout
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "HEAD"])
        )
        s.mount("https://", HTTPAdapter(max_retries=retry))
        s.mount("http://", HTTPAdapter(max_retries=retry))
        return s

    def fetch(self) -> str:
        """
        Gọi API và trả về HTML (string). Ném exception nếu lỗi mạng hoặc mã trạng thái không OK.
        """
        resp = self._session.get(self.api_url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()

        # Chọn encoding hợp lý để trả về text chính xác
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding

        return resp.text

