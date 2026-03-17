"""
InsightDoc API 客户端
"""

import json
import time
import requests
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Optional


class InsightDocClient:
    """InsightDoc 文档解析 API 客户端"""

    BASE_URL = "https://insightdoc.memect.cn"

    def __init__(self, api_key: str):
        if not api_key or not api_key.strip():
            raise ValueError("API Key 不能为空，请通过环境变量 INSIGHTDOC_API_KEY 或 --api-key 参数提供")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key.strip()}"
        })

    def create_task(
        self,
        file_path: str,
        task_type: str = "docparse",
        file_name: Optional[str] = None,
        task_param: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """上传文件创建解析任务"""
        url = f"{self.BASE_URL}/api/tasks"
        if not file_name:
            file_name = Path(file_path).name

        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "application/octet-stream")}
            data = {"task_type": task_type, "file_name": file_name}
            if task_param:
                data["task_param"] = json.dumps(task_param)
            resp = self.session.post(url, files=files, data=data, verify=False)

        self._check_response(resp)
        return resp.json()

    def get_task_detail(
        self,
        task_id: str,
        result_type: Optional[str] = None,
        extra_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """获取任务详情"""
        url = f"{self.BASE_URL}/api/tasks/detail/{task_id}"
        params: Dict[str, str] = {}
        if result_type:
            params["result_type"] = result_type
        if extra_info:
            params["extra_info"] = json.dumps(extra_info)

        resp = self.session.get(url, params=params, verify=False)
        self._check_response(resp)
        return resp.json()

    def wait_for_completion(
        self,
        task_id: str,
        max_wait: int = 600,
        initial_interval: int = 2,
        max_interval: int = 30,
    ) -> Dict[str, Any]:
        """轮询等待任务完成（指数退避）"""
        start = time.time()
        interval = initial_interval

        while time.time() - start < max_wait:
            detail = self.get_task_detail(task_id)
            status = detail.get("status", "unknown")

            if status == "done":
                return detail
            if status == "failed":
                raise RuntimeError(f"任务失败: {detail}")

            print(f"  状态: {status}，{interval:.0f}s 后重试...")
            time.sleep(interval)
            interval = min(interval * 1.5, max_interval)

        raise TimeoutError(f"任务在 {max_wait}s 内未完成")

    def export_task(self, task_id: str, format_type: str = "json") -> bytes:
        """导出任务结果"""
        url = f"{self.BASE_URL}/api/tasks/{task_id}/export"
        resp = self.session.get(url, params={"format": format_type}, verify=False)
        self._check_response(resp)
        return resp.content

    def list_tasks(
        self,
        page: int = 1,
        page_size: int = 10,
        task_name: Optional[str] = None,
        task_status: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取历史任务列表"""
        url = f"{self.BASE_URL}/api/tasks/history"
        params: Dict[str, Any] = {"page": page, "page_size": min(page_size, 100)}
        if task_name:
            params["task_name"] = task_name
        if task_status:
            params["task_status"] = task_status
        if task_type:
            params["task_type"] = task_type

        resp = self.session.get(url, params=params, verify=False)
        self._check_response(resp)
        return resp.json()

    @staticmethod
    def download_file(url: str, dest_dir: Optional[str] = None) -> str:
        """下载远程文件到本地临时目录，返回本地路径"""
        parsed = urllib.parse.urlparse(url)
        filename = Path(parsed.path).name or "downloaded_file.pdf"

        if dest_dir:
            dest = Path(dest_dir) / filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            local_path = str(dest)
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}")
            local_path = tmp.name
            tmp.close()

        print(f"  下载: {url}")
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()

        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  已保存到: {local_path}")
        return local_path

    @staticmethod
    def _check_response(resp: requests.Response) -> None:
        if resp.status_code == 401:
            raise PermissionError("认证失败: API Key 无效或已过期，请检查 INSIGHTDOC_API_KEY")
        if resp.status_code == 422:
            raise ValueError(f"参数错误: {resp.text}")
        if resp.status_code != 200:
            raise RuntimeError(f"API 请求失败 [{resp.status_code}]: {resp.text}")
