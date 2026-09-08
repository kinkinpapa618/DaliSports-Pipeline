"""
Gemini Key & Model Rotation Engine for AgentX
Cơ chế xoay tua Round-Robin đa API Key và đa Model (Gemini 3.6 Flash, 3.5 Flash, 3.1 Flash-Lite, v.v.)
Tự động Failover khi gặp 429 (Rate limit / Quota), 403 (IP restriction), 503 (High demand) hoặc 404 (Deprecated).
"""

import os
import time
import httpx
import threading
from typing import List, Dict, Any, Optional, Tuple

# Danh sách 17 Gemini API Keys mặc định từ hệ thống
DEFAULT_GEMINI_KEYS: List[str] = [
    "AQ.Ab8RN6KJrYldy3Vat0MUiQIEbTCkcCiEjbYiicdUxu73BAA-9g",
    "AQ.Ab8RN6IEUCBRPd43YqZnI9J2CXpWQk9aChajZ0P9-lTx55STJQ",
    "AQ.Ab8RN6LovxfTxAH89Hjs2KUoooR0VvNRg3xfka-WgUNq8lXE2Q",
    "AQ.Ab8RN6Lcg9ymSt6qpNhvbrFmPv39eUUG33ESH91H6-orQzLxaw",
    "AQ.Ab8RN6I65I4g6PeSuDWsfiJw1npCfZ5qFI6w5qCTc1tR9O-YMQ",
    "AQ.Ab8RN6K508PWslvB8FszoUtO8BwnHmWphXmn0e_E_rF96QdYOw",
    "AIzaSyDHytCA5dy4MqxAXixQANZ4TIIDj69G3Dg",
    "AIzaSyBjZXVkCwf-D0hI7E4qGzxhNVfgtfeSR80",
    "AIzaSyDSmEKfw8eabrGBmxxFq6KKk-wNUbQw-_s",
    "AIzaSyB20LddCyDqdhtb8JbuJ0G0_Dup55zsw6s",
    "AIzaSyDVNfOnJUSz51v1ac5YIgYdSWJHJOSyxxg",
    "AQ.Ab8RN6II7EzV6Rqc8Vrzl5qZU54r4NKuRo-XtVyVch7_RVd5rg",
    "AIzaSyAlg69et4zvKv6DW__9ZHQZVvYObhWiLO4",
    "AIzaSyDsoJGXbtWqicqEqbIMHMxHgAwPpFQ2KLE",
    "AIzaSyAAWLhv5JQhR7P7ZjZGwtQev6KB-poT8VQ",
    "AIzaSyCtqkPJNpp7by04WDa0wZjRdSGXXsVAYU8",
    "AIzaSyDxZIVIUrzlWacLHMZW5R0czXwJ8Y6S2zk",
]

# Danh sách các Model Gemini được kiểm tra thực tế hoạt động ổn định nhất
RECOMMENDED_GEMINI_MODELS: List[str] = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview",
    "gemini-3.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

class GeminiRotator:
    _lock = threading.Lock()
    _current_index = 0
    _cooldowns: Dict[str, float] = {}  # key -> cooldown_until timestamp
    _stats: Dict[str, Dict[str, int]] = {}  # key -> {success, errors, 429_count}

    @classmethod
    def mask_key(cls, key: str) -> str:
        """Che bớt ký tự của key để log an toàn"""
        if not key:
            return "empty"
        if len(key) <= 10:
            return key[:3] + "..."
        return f"{key[:7]}...{key[-5:]}"

    @classmethod
    def get_all_keys(cls, custom_key: Optional[str] = None) -> List[str]:
        """
        Lấy danh sách toàn bộ API keys:
        1. Key người dùng truyền trực tiếp (nếu có)
        2. Key trong biến môi trường GEMINI_API_KEYS (ngăn cách bởi dấu phẩy hoặc xuống dòng)
        3. Key đơn trong GEMINI_API_KEY hoặc GOOGLE_API_KEY
        4. Danh sách 17 keys mặc định
        """
        keys_set = []

        # 1. Custom key
        if custom_key:
            for k in custom_key.replace("\n", ",").split(","):
                k = k.strip().strip('"').strip("'")
                if k and k not in keys_set:
                    keys_set.append(k)

        # 2. Env multi-keys
        env_multi = os.environ.get("GEMINI_API_KEYS", "")
        if env_multi:
            for k in env_multi.replace("\n", ",").split(","):
                k = k.strip().strip('"').strip("'")
                if k and k not in keys_set:
                    keys_set.append(k)

        # 3. Env single keys
        for env_var in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
            k = os.environ.get(env_var, "").strip().strip('"').strip("'")
            if k and k not in keys_set:
                keys_set.append(k)

        # 4. Default 17 keys pool
        for k in DEFAULT_GEMINI_KEYS:
            if k not in keys_set:
                keys_set.append(k)

        return keys_set

    @classmethod
    def _get_ordered_keys(cls, all_keys: List[str]) -> List[str]:
        """Sắp xếp key theo lượt xoay vòng (round-robin) và ưu tiên key không bị cooldown"""
        now = time.time()
        with cls._lock:
            start_idx = cls._current_index % len(all_keys)
            cls._current_index = (cls._current_index + 1) % len(all_keys)

        # Tạo chuỗi xoay vòng từ start_idx
        rotated = all_keys[start_idx:] + all_keys[:start_idx]

        # Phân loại: key sẵn sàng vs key đang cooldown
        ready_keys = []
        cooldown_keys = []

        for k in rotated:
            cooldown_until = cls._cooldowns.get(k, 0)
            if now >= cooldown_until:
                ready_keys.append(k)
            else:
                cooldown_keys.append(k)

        # Ưu tiên các key sẵn sàng, sau đó mới thử các key trong cooldown nếu cần
        return ready_keys + cooldown_keys

    @classmethod
    def mark_key_result(cls, key: str, success: bool, error_code: Optional[int] = None, error_msg: str = ""):
        """Ghi nhận trạng thái key để điều tiết xoay tua"""
        now = time.time()
        with cls._lock:
            if key not in cls._stats:
                cls._stats[key] = {"success": 0, "errors": 0, "rate_limited": 0}

            if success:
                cls._stats[key]["success"] += 1
                cls._cooldowns.pop(key, None)
            else:
                cls._stats[key]["errors"] += 1
                if error_code == 429:
                    cls._stats[key]["rate_limited"] += 1
                    # Cooldown 45 giây khi gặp quota / rate limit
                    cls._cooldowns[key] = now + 45.0
                elif error_code == 403:
                    # IP restriction hoặc key cấm -> Cooldown 1 giờ
                    cls._cooldowns[key] = now + 3600.0
                elif error_code in [500, 503]:
                    # Server Google quá tải -> Cooldown 15 giây
                    cls._cooldowns[key] = now + 15.0

    @classmethod
    def image_to_base64(cls, image_input: Any) -> Tuple[str, str]:
        """Chuyển đổi PIL Image / file path / bytes / numpy array sang base64 & media_type (Tự động tối ưu dung lượng)"""
        import io
        import base64
        from PIL import Image
        
        # 1. PIL Image
        if hasattr(image_input, "save") and hasattr(image_input, "convert"):
            img = image_input.convert("RGB")
            max_dim = max(img.width, img.height)
            if max_dim > 1920:
                scale = 1920.0 / max_dim
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88)
            return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/jpeg"
        
        # 2. Numpy ndarray (từ cv2.imread / video frame)
        if hasattr(image_input, "shape") and hasattr(image_input, "dtype"):
            try:
                import cv2
                _, encoded = cv2.imencode(".jpg", image_input, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
                return base64.b64encode(encoded.tobytes()).decode("utf-8"), "image/jpeg"
            except Exception:
                pass
        
        # 3. File path
        if isinstance(image_input, str) and os.path.exists(image_input):
            with open(image_input, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(image_input)[1].lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            return b64, mime
        
        # 4. Data URI or raw base64 string
        if isinstance(image_input, str):
            clean_str = image_input.strip()
            if clean_str.startswith("data:"):
                parts = clean_str.split(",", 1)
                mime = parts[0].split(";")[0].replace("data:", "") if "image/" in parts[0] else "image/jpeg"
                return parts[1], mime
            return clean_str, "image/jpeg"
        
        # 5. Raw bytes
        if isinstance(image_input, bytes):
            return base64.b64encode(image_input).decode("utf-8"), "image/jpeg"
        
        raise ValueError(f"Không thể chuyển đổi {type(image_input)} sang base64 image")

    @classmethod
    def generate_vision_sync(
        cls,
        prompt_text: str,
        image_input: Any,
        preferred_model: Optional[str] = None,
        custom_key: Optional[str] = None,
        timeout: float = 35.0
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Gọi Gemini Vision đồng bộ (Sync) với cơ chế xoay tua 17 keys và đa models.
        """
        image_base64, media_type = cls.image_to_base64(image_input)
        all_keys = cls.get_all_keys(custom_key)
        
        models = []
        if preferred_model:
            models.append(preferred_model)
        for m in RECOMMENDED_GEMINI_MODELS:
            if m not in models:
                models.append(m)

        ordered_keys = cls._get_ordered_keys(all_keys)
        last_error = None
        attempt_count = 0

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": media_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1
            }
        }

        with httpx.Client(timeout=timeout) as client:
            for key in ordered_keys:
                masked_k = cls.mask_key(key)
                for model_name in models:
                    attempt_count += 1
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    
                    try:
                        resp = client.post(
                            url,
                            headers={"Content-Type": "application/json"},
                            json=payload
                        )
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            if "candidates" in data and len(data["candidates"]) > 0:
                                cand = data["candidates"][0]
                                if "content" in cand and "parts" in cand["content"] and len(cand["content"]["parts"]) > 0:
                                    content_text = cand["content"]["parts"][0].get("text", "")
                                    if content_text:
                                        cls.mark_key_result(key, success=True)
                                        return content_text, {
                                            "status": "success",
                                            "model_used": model_name,
                                            "key_used": masked_k,
                                            "attempts": attempt_count
                                        }

                        status_code = resp.status_code
                        err_data = {}
                        try:
                            err_data = resp.json().get("error", {})
                        except Exception:
                            pass
                        err_msg = err_data.get("message", resp.text[:150])
                        cls.mark_key_result(key, success=False, error_code=status_code, error_msg=err_msg)
                        last_error = f"[{model_name} | {masked_k}] HTTP {status_code}: {err_msg}"

                        if status_code in [403, 400] and ("API_KEY_INVALID" in err_msg or "IP address restriction" in err_msg):
                            break

                    except Exception as e:
                        last_error = f"[{model_name} | {masked_k}] Lỗi mạng: {str(e)}"
                        cls.mark_key_result(key, success=False, error_code=500, error_msg=str(e))
                        continue

        return None, {
            "status": "error",
            "last_error": last_error or "Không kết nối được Gemini",
            "attempts": attempt_count
        }

    @classmethod
    async def generate_vision_content(
        cls,
        prompt_text: str,
        image_base64: Any,
        media_type: str = "image/png",
        custom_key: Optional[str] = None,
        models_to_try: Optional[List[str]] = None,
        timeout: float = 40.0
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Gửi yêu cầu Vision tới Gemini với cơ chế xoay tua API Key & Model tự động.
        Trả về (content_text, metadata_info)
        """
        if not isinstance(image_base64, str) or not image_base64.startswith("data:"):
            try:
                image_base64, media_type = cls.image_to_base64(image_base64)
            except Exception:
                pass

        all_keys = cls.get_all_keys(custom_key)
        models = models_to_try or RECOMMENDED_GEMINI_MODELS
        ordered_keys = cls._get_ordered_keys(all_keys)

        last_error = None
        attempt_count = 0

        # Chuẩn bị payload inline_data
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": media_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            for key in ordered_keys:
                masked_k = cls.mask_key(key)
                
                for model_name in models:
                    attempt_count += 1
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    
                    try:
                        resp = await client.post(
                            url,
                            headers={"Content-Type": "application/json"},
                            json=payload
                        )
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            if "candidates" in data and len(data["candidates"]) > 0:
                                cand = data["candidates"][0]
                                if "content" in cand and "parts" in cand["content"] and len(cand["content"]["parts"]) > 0:
                                    content_text = cand["content"]["parts"][0].get("text", "")
                                    if content_text:
                                        cls.mark_key_result(key, success=True)
                                        meta = {
                                            "status": "success",
                                            "model_used": model_name,
                                            "key_used": masked_k,
                                            "attempts": attempt_count
                                        }
                                        return content_text, meta

                        # Xử lý lỗi từ Google API
                        status_code = resp.status_code
                        err_data = {}
                        try:
                            err_data = resp.json().get("error", {})
                        except Exception:
                            pass
                        
                        err_msg = err_data.get("message", resp.text[:200])
                        cls.mark_key_result(key, success=False, error_code=status_code, error_msg=err_msg)
                        last_error = f"[{model_name} | {masked_k}] HTTP {status_code}: {err_msg}"

                        # Nếu gặp 403 (IP restriction) hoặc 400 (Bad request key) -> bỏ qua toàn bộ model của key này
                        if status_code in [403, 400] and ("API_KEY_INVALID" in err_msg or "IP address restriction" in err_msg):
                            break

                    except Exception as e:
                        last_error = f"[{model_name} | {masked_k}] Connection error: {str(e)}"
                        cls.mark_key_result(key, success=False, error_code=500, error_msg=str(e))
                        continue

        return None, {
            "status": "error",
            "last_error": last_error or "Không thể kết nối tới Google Gemini",
            "attempts": attempt_count
        }

    @classmethod
    async def generate_text_content(
        cls,
        prompt_text: str,
        system_instruction: Optional[str] = None,
        custom_key: Optional[str] = None,
        models_to_try: Optional[List[str]] = None,
        timeout: float = 30.0
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Gửi yêu cầu phân tích văn bản / số liệu tới Gemini qua cơ chế xoay tua API Key & Model.
        """
        all_keys = cls.get_all_keys(custom_key)
        models = models_to_try or RECOMMENDED_GEMINI_MODELS
        ordered_keys = cls._get_ordered_keys(all_keys)

        full_prompt = f"{system_instruction}\n\n{prompt_text}" if system_instruction else prompt_text
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
            }
        }

        last_error = None
        attempt_count = 0

        async with httpx.AsyncClient(timeout=timeout) as client:
            for key in ordered_keys:
                masked_k = cls.mask_key(key)
                for model_name in models:
                    attempt_count += 1
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    try:
                        resp = await client.post(
                            url,
                            headers={"Content-Type": "application/json"},
                            json=payload
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if "candidates" in data and len(data["candidates"]) > 0:
                                content_text = data["candidates"][0]["content"]["parts"][0].get("text", "")
                                if content_text:
                                    cls.mark_key_result(key, success=True)
                                    return content_text, {
                                        "status": "success",
                                        "model_used": model_name,
                                        "key_used": masked_k,
                                        "attempts": attempt_count
                                    }

                        status_code = resp.status_code
                        err_msg = resp.text[:200]
                        cls.mark_key_result(key, success=False, error_code=status_code, error_msg=err_msg)
                        last_error = f"[{model_name} | {masked_k}] HTTP {status_code}: {err_msg}"

                        if status_code in [403, 400] and ("API_KEY_INVALID" in err_msg or "IP address restriction" in err_msg):
                            break
                    except Exception as e:
                        last_error = f"[{model_name} | {masked_k}] Connection error: {str(e)}"
                        cls.mark_key_result(key, success=False, error_code=500, error_msg=str(e))
                        continue

        return None, {
            "status": "error",
            "last_error": last_error or "Không thể kết nối tới Google Gemini",
            "attempts": attempt_count
        }

    @classmethod
    def get_pool_status(cls) -> Dict[str, Any]:
        """Lấy thông tin trạng thái tải và danh sách key trong Pool"""
        all_keys = cls.get_all_keys()
        now = time.time()
        
        status_list = []
        for idx, k in enumerate(all_keys):
            cooldown_until = cls._cooldowns.get(k, 0)
            is_cooldown = now < cooldown_until
            remaining = max(0, int(cooldown_until - now)) if is_cooldown else 0
            stats = cls._stats.get(k, {"success": 0, "errors": 0, "rate_limited": 0})
            
            status_list.append({
                "index": idx + 1,
                "key_masked": cls.mask_key(k),
                "is_active": not is_cooldown,
                "cooldown_seconds": remaining,
                "success_count": stats["success"],
                "error_count": stats["errors"],
                "rate_limited_count": stats["rate_limited"]
            })

        return {
            "total_keys": len(all_keys),
            "available_models": RECOMMENDED_GEMINI_MODELS,
            "keys_status": status_list
        }
