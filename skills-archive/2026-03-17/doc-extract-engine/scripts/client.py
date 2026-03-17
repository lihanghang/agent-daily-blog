"""
文档提取引擎 API 客户端

封装完整提取流程：认证 → 上传 → Schema设计 → 提取 → 修正 → 归档
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import httpx


class ExtractEngineClient:
    """文档提取引擎 API 客户端"""

    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client = httpx.Client(timeout=60.0)
        if token:
            self._client.headers["Authorization"] = f"Bearer {token}"

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _check(self, resp: httpx.Response) -> Dict[str, Any]:
        # 先尝试解析 JSON 获取业务错误信息，再决定是否抛异常
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            raise RuntimeError(f"API 返回非 JSON 响应: {resp.text[:200]}")

        if resp.status_code >= 400:
            msg = data.get("message") or data.get("detail") or resp.text[:200]
            raise RuntimeError(f"API 错误 [{resp.status_code}]: {msg}")

        if not data.get("success", False):
            raise RuntimeError(f"API 错误: {data.get('message', '未知错误')}")
        return data.get("data", {})

    # ── 认证 ──

    def register(self, username: str, password: str, email: str) -> Dict[str, Any]:
        """用户注册"""
        resp = self._client.post(
            f"{self.base_url}/api/v1/auth/register",
            json={"username": username, "password": password, "email": email},
        )
        return self._check(resp)

    def login(self, username: str, password: str) -> str:
        """登录并返回 access_token，同时更新客户端认证头"""
        resp = self._client.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        data = self._check(resp)
        self.token = data["access_token"]
        self._client.headers["Authorization"] = f"Bearer {self.token}"
        return self.token

    # ── 文档管理 ──

    def upload_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """上传 1-3 个 PDF 文件，返回文档信息列表"""
        if not 1 <= len(file_paths) <= 3:
            raise ValueError("每次上传 1-3 个文件")
        files = []
        for p in file_paths:
            path = Path(p)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {p}")
            files.append(("files", (path.name, open(p, "rb"), "application/pdf")))
        try:
            resp = self._client.post(
                f"{self.base_url}/api/v1/documents/upload",
                files=files,
                headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            )
            data = self._check(resp)
            return data["documents"]
        finally:
            for _, (_, f, _) in files:
                f.close()

    # ── Schema 对话 ──

    def create_schema_conversation(self, document_ids: List[str]) -> int:
        """创建 Schema 对话，返回 conversation_id"""
        resp = self._client.post(
            f"{self.base_url}/api/v1/session/schema-conversation/create",
            json={"document_ids": document_ids},
            headers=self._headers(),
        )
        return self._check(resp)["conversation_id"]

    def chat_schema(
        self,
        conversation_id: int,
        message: str,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Schema 对话（SSE 流式），返回最终 schema"""
        return self._consume_sse(
            f"{self.base_url}/api/v1/session/schema-conversation/{conversation_id}/chat",
            {"message": message},
            on_event=on_event,
        )

    def get_schema_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """获取 Schema 对话状态"""
        resp = self._client.get(
            f"{self.base_url}/api/v1/session/schema-conversation/{conversation_id}",
            headers=self._headers(),
        )
        return self._check(resp)

    # ── Session 管理 ──

    def create_session(
        self,
        session_name: str,
        schema_json: Dict[str, Any],
        document_ids: List[str],
    ) -> int:
        """创建提取 Session，返回 session_id"""
        resp = self._client.post(
            f"{self.base_url}/api/v1/session/create",
            json={
                "session_name": session_name,
                "schema_json": schema_json,
                "initial_document_ids": document_ids,
            },
            headers=self._headers(),
        )
        return self._check(resp)["session_id"]

    def list_sessions(self) -> List[Dict[str, Any]]:
        """获取 Session 列表"""
        resp = self._client.get(
            f"{self.base_url}/api/v1/session/list",
            headers=self._headers(),
        )
        return self._check(resp)["sessions"]

    def load_session(self, session_id: int) -> Dict[str, Any]:
        """加载 Session 详情"""
        resp = self._client.get(
            f"{self.base_url}/api/v1/session/load",
            params={"session_id": session_id},
            headers=self._headers(),
        )
        return self._check(resp)

    # ── 提取 ──

    def extract(
        self,
        session_id: int,
        document_ids: List[str],
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """执行文档提取（SSE 流式），返回 {batch_id, results}"""
        return self._consume_sse(
            f"{self.base_url}/api/v1/extract",
            {"session_id": session_id, "documents_list": document_ids},
            on_event=on_event,
        )

    # ── 对话修正 ──

    def chat_correct(
        self,
        batch_id: int,
        message: str,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """对话修正提取结果（SSE 流式）"""
        return self._consume_sse(
            f"{self.base_url}/api/v1/chat/{batch_id}",
            {"message": message},
            on_event=on_event,
        )

    # ── 归档 ──

    def end_batch(self, batch_id: int) -> Dict[str, Any]:
        """结束 Batch 并归档"""
        resp = self._client.post(
            f"{self.base_url}/api/v1/batch/end/{batch_id}",
            headers=self._headers(),
        )
        return self._check(resp)

    # ── 历史查询 ──

    def get_history(self, session_id: int) -> List[Dict[str, Any]]:
        """查看历史提取结果"""
        resp = self._client.get(
            f"{self.base_url}/api/v1/history/{session_id}",
            headers=self._headers(),
        )
        return self._check(resp)["results"]

    # ── SSE 流式消费 ──

    def _consume_sse(
        self,
        url: str,
        body: Dict[str, Any],
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """消费 SSE 流，收集结果并回调事件"""
        collected = {"batch_id": None, "results": [], "schema": None, "messages": []}

        with httpx.Client(timeout=None) as client:
            with client.stream(
                "POST",
                url,
                json=body,
                headers=self._headers(),
            ) as resp:
                resp.raise_for_status()
                buffer = ""
                for chunk in resp.iter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue
                        try:
                            event = json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue

                        if on_event:
                            on_event(event)

                        etype = event.get("type", "")
                        if etype == "batch_created":
                            collected["batch_id"] = event.get("batch_id")
                        elif etype == "result_update":
                            collected["results"] = event.get("content", [])
                        elif etype == "schema_updated":
                            collected["schema"] = event.get("schema")
                        elif etype == "message":
                            collected["messages"].append(event.get("content", ""))
                        elif etype == "error":
                            raise RuntimeError(f"SSE 错误: {event.get('message')}")
                        elif etype == "done":
                            break

        return collected

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
