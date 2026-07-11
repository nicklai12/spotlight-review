from abc import ABC, abstractmethod


class BaseSourceAdapter(ABC):
    """每個 AI 工具的 session 讀取器必須繼承這個 class。
    唯一的責任：找到最新的 session 檔案，回傳符合統一 Schema 1 的 dict。"""

    @abstractmethod
    def find_latest_session(self) -> str:
        """
        回傳最新 session 的「原始來源路徑」（檔案路徑或 DB 路徑）。
        找不到 → raise ValueError，訊息說明找哪個路徑
        """
        pass

    @abstractmethod
    def read_session(self, source_path: str) -> list[dict]:
        """讀取並解析 session，回傳統一格式的 list[dict]。
        每個 dict 的 key：role / tool / path / command / content / timestamp
        不在規格內的欄位統一填 None。"""
        pass

    def collect(self) -> dict:
        """組合以上兩個方法，回傳完整的 Schema 1 dict。"""
        from datetime import datetime
        source_path = self.find_latest_session()
        session_raw = self.read_session(source_path)
        return {
            "session_file": source_path,
            "session_raw": session_raw,
            "session_id": self._extract_session_id(source_path),
            "timestamp": datetime.utcnow().isoformat(),
            "source_type": self.SOURCE_TYPE,
        }

    def _extract_session_id(self, path: str) -> str:
        import os
        return os.path.splitext(os.path.basename(path))[0] or "session_unknown"
