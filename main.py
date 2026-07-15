"""
Claude Code 管理工具 - 适配版
基于 aikun-gui 架构，针对 Claude Code 专门优化
使用自定义 Logo 和品牌设计
"""

import json
import os
import platform
import subprocess
import sys
import time
import webbrowser
import webview
import requests
from pathlib import Path

# ============================================================
#  常量
# ============================================================

PLATFORM = platform.system()
CONFIG_DIR = Path.home() / ".claude"
CONFIG_FILE = CONFIG_DIR / "settings.json"
PLUGINS_DIR = CONFIG_DIR / "plugins"
ZHCN_REPO_DIR = PLUGINS_DIR / "claude-code-zh-cn"
CACHE_DIR = Path.home() / ".claude-manager"
SESSION_FILE = CACHE_DIR / "session.json"

# 默认 API 配置
DEFAULT_BASE_URL = "https://aikun.cnzc.qzz.io"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
AIKUN_SITE = "https://aikun.cnzc.qzz.io"

# ============================================================
#  工具函数
# ============================================================

def run_cmd(cmd, cwd=None, timeout=30):
    """执行命令并返回输出"""
    try:
        si = None
        if PLATFORM == "Windows":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
        
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=cwd, timeout=timeout, startupinfo=si
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "命令超时", 1
    except Exception as e:
        return "", str(e), 1

def load_config():
    """加载配置"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_config(cfg):
    """保存配置"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def load_session():
    """加载 Session"""
    try:
        if SESSION_FILE.exists():
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_session(data):
    """保存 Session"""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def clear_session():
    """清除 Session"""
    try:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
        return True
    except:
        return False

def detect_claude():
    """自动检测 Claude Code 安装路径"""
    paths_found = []
    
    if PLATFORM == "Windows":
        # 方法1: npm 全局安装路径
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            npm_path = Path(appdata) / "npm" / "node_modules" / "@anthropic-ai" / "claude-code"
            if npm_path.exists():
                paths_found.append(str(npm_path))
        
        # 方法2: where claude
        out, _, rc = run_cmd("where claude")
        if rc == 0 and out:
            for line in out.split("\n"):
                line = line.strip()
                if line and Path(line).exists():
                    paths_found.append(str(Path(line).parent.parent))
        
        # 方法3: 常见安装位置
        common_paths = [
            Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "@anthropic-ai" / "claude-code",
            Path("C:/Program Files/nodejs/node_modules/@anthropic-ai/claude-code"),
            Path("C:/Program Files (x86)/nodejs/node_modules/@anthropic-ai/claude-code"),
        ]
        for p in common_paths:
            if p.exists() and str(p) not in paths_found:
                paths_found.append(str(p))
    else:
        # macOS/Linux
        out, _, rc = run_cmd("which claude")
        if rc == 0 and out:
            for line in out.split("\n"):
                line = line.strip()
                if line and Path(line).exists():
                    paths_found.append(str(Path(line).parent.parent))
        
        # 常见安装位置
        common_paths = [
            Path.home() / ".npm" / "node_modules" / "@anthropic-ai" / "claude-code",
            Path("/usr/local/lib/node_modules/@anthropic-ai/claude-code"),
            Path("/usr/lib/node_modules/@anthropic-ai/claude-code"),
        ]
        for p in common_paths:
            if p.exists() and str(p) not in paths_found:
                paths_found.append(str(p))
    
    return paths_found

# ============================================================
#  API Bridge
# ============================================================

class ApiBridge:
    """pywebview JavaScript API Bridge"""
    
    # ---- 仪表盘 ----
    
    def get_dashboard(self):
        """获取仪表盘数据"""
        try:
            cfg = load_config()
            
            # 检测 Claude 安装
            claude_paths = detect_claude()
            claude_installed = len(claude_paths) > 0
            claude_path = claude_paths[0] if claude_paths else ""
            
            # 检查 claude 命令是否可用
            claude_cmd_available = False
            claude_version = ""
            if claude_installed:
                out, _, rc = run_cmd("claude --version")
                if rc == 0:
                    claude_cmd_available = True
                    claude_version = out.strip()
            
            # API 配置状态 - 从env对象中读取
            env = cfg.get("env", {})
            base_url = env.get("ANTHROPIC_BASE_URL", "")
            api_key = env.get("ANTHROPIC_AUTH_TOKEN", "")
            model = env.get("ANTHROPIC_MODEL", "")
            has_api = bool(base_url and api_key)
            
            # 思考程度（优先从环境变量读取）
            effort_level = cfg.get("env", {}).get("CLAUDE_CODE_EFFORT_LEVEL", "")
            if not effort_level:
                effort_level = cfg.get("effortLevel", "medium")
            
            # 汉化补丁状态
            patch_info = self._get_patch_status()
            
            return {
                "ok": True,
                "platform": PLATFORM,
                "claude_installed": claude_installed,
                "claude_cmd_available": claude_cmd_available,
                "claude_version": claude_version,
                "claude_path": claude_path,
                "has_api": has_api,
                "base_url": base_url,
                "api_key_masked": self._mask_key(api_key),
                "model": model or "未设置",
                "effort_level": effort_level,
                "patch_status": patch_info.get("status_text", "未知"),
                "config_file": str(CONFIG_FILE),
            }
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def _mask_key(self, key):
        """遮蔽 API Key"""
        if not key:
            return ""
        if len(key) > 8:
            return key[:8] + "****"
        return "****"
    
    def _get_patch_status(self):
        """获取汉化补丁状态（详细）"""
        result = {
            "settings_ok": False,
            "plugin_enabled": False,
            "binary_patched": False,
            "binary_version": "",
            "patch_version": "",
            "install_type": "unknown",
            "status_text": "未知",
        }
        try:
            # 检查汉化仓库（多个可能的位置）
            repo_dir = CONFIG_DIR / "claude-code-zh-cn-repo"
            plugin_dir = ZHCN_REPO_DIR  # ~/.claude/plugins/claude-code-zh-cn
            
            # 确定使用的目录
            if repo_dir.exists():
                active_dir = repo_dir
            elif plugin_dir.exists():
                active_dir = plugin_dir
            else:
                result["status_text"] = "仓库未安装"
                return result
            
            # 检查 settings.json 配置
            cfg = load_config()
            lang = cfg.get("language", "")
            spinner = cfg.get("spinnerVerbs", {})
            enabled_plugins = cfg.get("enabledPlugins", {})
            plugin_enabled = enabled_plugins.get("claude-code-zh-cn@claude-code-zh-cn", False)
            result["plugin_enabled"] = plugin_enabled
            
            spinner_mode = ""
            if isinstance(spinner, dict):
                spinner_mode = spinner.get("mode", "")
            elif isinstance(spinner, str):
                spinner_mode = spinner
            
            settings_ok = (lang == "Chinese" and spinner_mode == "replace")
            result["settings_ok"] = settings_ok
            
            # 检测 Claude 安装类型和二进制补丁状态
            claude_bin = self._find_claude_binary()
            if claude_bin:
                # 检测安装类型
                helper = active_dir / "bun-binary-io.js"
                if helper.exists():
                    out, _, rc = run_cmd(f'node "{helper}" detect "{claude_bin}"', timeout=10)
                    if rc == 0 and out.strip():
                        parts = out.strip().split(":", 1)
                        result["install_type"] = parts[0]  # native-bun or npm
                
                # 获取二进制版本
                if result["install_type"] == "native-bun" and helper.exists():
                    out, _, _ = run_cmd(f'node "{helper}" version "{claude_bin}"', timeout=10)
                    result["binary_version"] = out.strip()
                else:
                    out, _, _ = run_cmd(f'claude --version', timeout=10)
                    ver_match = out.strip().split()
                    result["binary_version"] = ver_match[0] if ver_match else ""
            
            # 检查 .patched-version 标记（两个位置都检查）
            marker_file = active_dir / ".patched-version"
            if not marker_file.exists():
                marker_file = plugin_dir / ".patched-version"
            if marker_file.exists():
                marker = marker_file.read_text(encoding="utf-8").strip()
                if marker.startswith("native|"):
                    parts = marker.split("|")
                    if len(parts) >= 2:
                        result["patch_version"] = parts[1]
                        result["binary_patched"] = (parts[1] == result["binary_version"])
                elif marker:
                    # npm 模式
                    result["patch_version"] = marker.split("|")[0] if "|" in marker else marker
                    result["binary_patched"] = True
            
            # 综合判断状态
            if result["binary_patched"] and settings_ok and plugin_enabled:
                result["status_text"] = "已打补丁"
            elif result["binary_patched"] and settings_ok:
                result["status_text"] = "已打补丁（插件未启用）"
            elif result["binary_patched"]:
                result["status_text"] = "二进制已补丁（设置未完成）"
            elif settings_ok and plugin_enabled:
                result["status_text"] = "设置已配置（二进制未补丁）"
            elif settings_ok:
                result["status_text"] = "设置已配置（插件未启用）"
            else:
                result["status_text"] = "未打补丁"
            
            return result
        except Exception as e:
            result["status_text"] = f"检测失败: {str(e)}"
            return result
    
    def _find_claude_binary(self):
        """查找 Claude Code 二进制文件路径"""
        try:
            cfg = load_config()
            
            # 优先使用用户手动设置的路径
            custom_path = cfg.get("claude_install_path", "")
            if custom_path and Path(custom_path).exists():
                if Path(custom_path).is_file():
                    return custom_path
                # 如果是目录，查找 claude.exe
                exe_path = Path(custom_path) / "bin" / "claude.exe"
                if exe_path.exists():
                    return str(exe_path)
            
            # 自动检测
            if PLATFORM == "Windows":
                # 方法1: where claude
                out, _, rc = run_cmd("where claude")
                if rc == 0 and out:
                    for line in out.strip().split("\n"):
                        line = line.strip()
                        if line and Path(line).exists():
                            return line
                
                # 方法2: npm 全局路径
                appdata = os.environ.get("APPDATA", "")
                if appdata:
                    npm_path = Path(appdata) / "npm" / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
                    if npm_path.exists():
                        return str(npm_path)
            else:
                # macOS/Linux
                out, _, rc = run_cmd("which claude")
                if rc == 0 and out:
                    return out.strip()
            
            return None
        except:
            return None
    
    # ---- Claude 路径管理 ----
    
    def scan_claude(self):
        """扫描 Claude Code 安装"""
        try:
            paths = detect_claude()
            return {
                "ok": True,
                "paths": paths,
                "count": len(paths)
            }
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def set_claude_path(self, path):
        """手动设置 Claude 路径"""
        try:
            if not path:
                return {"ok": False, "msg": "路径不能为空"}
            
            p = Path(path)
            if not p.exists():
                return {"ok": False, "msg": "路径不存在"}
            
            # 保存到配置
            cfg = load_config()
            cfg["_claude_path"] = str(p)
            save_config(cfg)
            
            return {"ok": True, "msg": f"已设置: {p}"}
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    # ---- API 配置 ----
    
    def get_api_config(self):
        """获取 API 配置"""
        try:
            cfg = load_config()
            env = cfg.get("env", {})
            return {
                "ok": True,
                "base_url": env.get("ANTHROPIC_BASE_URL", DEFAULT_BASE_URL),
                "api_key": env.get("ANTHROPIC_AUTH_TOKEN", ""),
                "model": env.get("ANTHROPIC_MODEL", ""),
                "sonnet_model": env.get("ANTHROPIC_DEFAULT_SONNET_MODEL", ""),
                "opus_model": env.get("ANTHROPIC_DEFAULT_OPUS_MODEL", ""),
                "haiku_model": env.get("ANTHROPIC_DEFAULT_HAIKU_MODEL", ""),
                "fable_model": env.get("ANTHROPIC_DEFAULT_FABLE_MODEL", ""),
            }
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def save_api_config(self, config):
        """保存 API 配置"""
        try:
            cfg = load_config()
            
            # 确保env对象存在
            if "env" not in cfg:
                cfg["env"] = {}
            
            # 保存 API Key 到env
            api_key = config.get("api_key", "")
            if api_key:
                cfg["env"]["ANTHROPIC_AUTH_TOKEN"] = api_key
            else:
                cfg["env"].pop("ANTHROPIC_AUTH_TOKEN", None)
            
            # 固定 Base URL 到env（不包含/v1，Claude Code会自动添加）
            cfg["env"]["ANTHROPIC_BASE_URL"] = "https://aikun.cnzc.qzz.io"
            
            # 删除顶层的旧配置（如果存在）
            cfg.pop("ANTHROPIC_AUTH_TOKEN", None)
            cfg.pop("ANTHROPIC_BASE_URL", None)
            cfg.pop("ANTHROPIC_MODEL", None)
            
            if save_config(cfg):
                return {"ok": True, "msg": "API 配置已保存"}
            return {"ok": False, "msg": "保存失败"}
        except Exception as e:
            return {"ok": False, "msg": f"保存失败: {str(e)}"}
    
    def save_effort_level(self, level):
        """保存思考程度（通过环境变量）"""
        try:
            if level not in ['low', 'medium', 'high']:
                return {"ok": False, "msg": "无效的思考程度，可选值: low, medium, high"}
            
            cfg = load_config()
            
            # 确保env对象存在
            if "env" not in cfg:
                cfg["env"] = {}
            
            # 通过环境变量设置思考程度
            cfg["env"]["CLAUDE_CODE_EFFORT_LEVEL"] = level
            
            # 同时保存到顶层（兼容性）
            cfg["effortLevel"] = level
            
            if save_config(cfg):
                return {"ok": True, "msg": f"思考程度已设置为: {level}"}
            return {"ok": False, "msg": "保存失败"}
        except Exception as e:
            return {"ok": False, "msg": f"保存失败: {str(e)}"}
    
    def get_effort_level(self):
        """获取当前思考程度"""
        try:
            cfg = load_config()
            # 优先从环境变量读取
            level = cfg.get("env", {}).get("CLAUDE_CODE_EFFORT_LEVEL", "")
            if not level:
                level = cfg.get("effortLevel", "medium")
            return {"ok": True, "level": level}
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    def get_model_list(self, config):
        """获取模型列表"""
        try:
            api_key = config.get("api_key", "")
            if not api_key:
                return {"ok": False, "msg": "请先填写 API Key"}
            
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            
            r = requests.get(
                "https://aikun.cnzc.qzz.io/v1/models",
                headers=headers,
                timeout=10
            )
            
            if r.status_code == 200:
                data = r.json()
                models = [m.get("id", "") for m in data.get("data", [])]
                return {"ok": True, "models": models}
            else:
                return {"ok": False, "msg": f"获取失败: HTTP {r.status_code}"}
        except Exception as e:
            return {"ok": False, "msg": f"获取失败: {str(e)}"}
    
    def test_api_connection(self, config):
        """测试 API 连接"""
        try:
            base_url = config.get("base_url", DEFAULT_BASE_URL)
            api_key = config.get("api_key", "")
            
            if not api_key:
                return {"ok": False, "msg": "请填写 API Key"}
            
            # 参考aikun-gui的方法：使用HEAD请求测试/models端点
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            # 构建URL
            if base_url.endswith('/v1'):
                url = f"{base_url}/models"
            else:
                url = f"{base_url}/v1/models"
            
            r = requests.head(
                url,
                headers=headers,
                timeout=5,
                allow_redirects=True
            )
            
            # 状态码小于500表示连接正常
            ok = r.status_code < 500
            
            if ok:
                return {"ok": True, "msg": "连接成功"}
            else:
                return {"ok": False, "msg": f"连接失败: HTTP {r.status_code}"}
        except requests.exceptions.Timeout:
            return {"ok": False, "msg": "连接超时"}
        except Exception as e:
            return {"ok": False, "msg": f"连接失败: {str(e)}"}
    
    def fetch_available_models(self, config):
        """获取可用模型列表"""
        try:
            base_url = config.get("base_url", DEFAULT_BASE_URL)
            api_key = config.get("api_key", "")
            
            if not api_key:
                return {"ok": False, "msg": "请先填写 API Key", "models": []}
            
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            # 构建URL
            if base_url.endswith('/v1'):
                url = f"{base_url}/models"
            else:
                url = f"{base_url}/v1/models"
            
            r = requests.get(url, headers=headers, timeout=15)
            
            if r.status_code != 200:
                return {"ok": False, "msg": f"API 返回 {r.status_code}", "models": []}
            
            models = [{"id": m["id"], "owned_by": m.get("owned_by", "")} for m in r.json().get("data", [])]
            return {"ok": True, "models": models}
        except Exception as e:
            return {"ok": False, "msg": str(e), "models": []}
    
    def save_model_config(self, config):
        """保存模型配置"""
        try:
            cfg = load_config()
            
            # 确保env对象存在
            if "env" not in cfg:
                cfg["env"] = {}
            
            # 保存默认模型到env
            if config.get("model"):
                cfg["env"]["ANTHROPIC_MODEL"] = config["model"]
            
            # 保存各个模型配置到env
            if config.get("sonnet_model"):
                cfg["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"] = config["sonnet_model"]
            
            if config.get("opus_model"):
                cfg["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] = config["opus_model"]
            
            if config.get("haiku_model"):
                cfg["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = config["haiku_model"]
            
            if config.get("fable_model"):
                cfg["env"]["ANTHROPIC_DEFAULT_FABLE_MODEL"] = config["fable_model"]
            
            # 删除顶层的旧配置（如果存在）
            cfg.pop("ANTHROPIC_MODEL", None)
            cfg.pop("ANTHROPIC_DEFAULT_SONNET_MODEL", None)
            cfg.pop("ANTHROPIC_DEFAULT_OPUS_MODEL", None)
            cfg.pop("ANTHROPIC_DEFAULT_HAIKU_MODEL", None)
            cfg.pop("ANTHROPIC_DEFAULT_FABLE_MODEL", None)
            
            if save_config(cfg):
                return {"ok": True, "msg": "模型配置已保存"}
            return {"ok": False, "msg": "保存失败"}
        except Exception as e:
            return {"ok": False, "msg": f"保存失败: {str(e)}"}
    
    def query_balance(self):
        """查询余额"""
        session_data = load_session()
        if not session_data.get("logged_in"):
            return {"ok": False, "balance": 0, "msg": "未登录", "need_login": True}

        try:
            cookies = session_data.get("cookies", {})
            user_id = session_data.get("user_id", 1)
            
            headers = {"New-Api-User": str(user_id)}
            r = requests.get(
                f"{AIKUN_SITE}/api/user/self",
                cookies=cookies,
                headers=headers,
                timeout=10
            )
            
            if r.status_code != 200:
                clear_session()
                return {"ok": False, "balance": 0, "msg": "Session 已过期，请重新登录", "need_login": True}

            data = r.json()
            if not data.get("success"):
                clear_session()
                return {"ok": False, "balance": 0, "msg": "Session 无效，请重新登录", "need_login": True}

            user = data.get("data", {})
            quota = user.get("quota", 0)
            used_quota = user.get("used_quota", 0)
            
            quota_per_unit = 500000
            balance = quota / quota_per_unit
            used = used_quota / quota_per_unit
            total = balance + used

            return {
                "ok": True,
                "total": round(total, 2),
                "used": round(used, 4),
                "balance": round(balance, 2),
                "msg": f"{balance:.2f} 积分",
                "username": user.get("username", ""),
                "logged_in": True
            }
        except Exception as e:
            return {"ok": False, "balance": 0, "msg": str(e)}
    
    # ---- 登录管理 ----
    
    def login_aikun(self, username, password):
        """登录 New-API 获取 Session"""
        if not username or not password:
            return {"ok": False, "msg": "用户名和密码不能为空"}

        try:
            session = requests.Session()
            
            login_data = {
                "username": username,
                "password": password
            }
            r = session.post(
                f"{AIKUN_SITE}/api/user/login",
                json=login_data,
                timeout=10
            )
            
            if r.status_code != 200:
                return {"ok": False, "msg": f"登录失败: HTTP {r.status_code}"}

            data = r.json()
            if not data.get("success"):
                return {"ok": False, "msg": data.get("message", "用户名或密码错误")}

            user_data = data.get("data", {})
            cookies = dict(session.cookies)
            
            save_session({
                "logged_in": True,
                "username": user_data.get("username", username),
                "user_id": user_data.get("id", 1),
                "cookies": cookies,
                "login_time": time.time()
            })

            return {
                "ok": True,
                "msg": f"登录成功，欢迎 {user_data.get('username', username)}",
                "username": user_data.get("username", username)
            }
        except Exception as e:
            return {"ok": False, "msg": f"登录失败: {str(e)}"}
    
    def logout_aikun(self):
        """退出登录"""
        session_data = load_session()
        if session_data.get("logged_in"):
            try:
                cookies = session_data.get("cookies", {})
                requests.get(
                    f"{AIKUN_SITE}/api/user/logout",
                    cookies=cookies,
                    timeout=5
                )
            except:
                pass
        clear_session()
        return {"ok": True, "msg": "已退出登录"}
    
    def get_login_status(self):
        """获取登录状态"""
        session_data = load_session()
        if session_data.get("logged_in"):
            return {
                "logged_in": True,
                "username": session_data.get("username", ""),
                "login_time": session_data.get("login_time", 0)
            }
        return {"logged_in": False}
    
    # ---- 汉化补丁 ----
    
    def get_patch_status(self):
        """获取汉化补丁状态（详细版）"""
        try:
            info = self._get_patch_status()
            info["ok"] = True
            # 检查汉化仓库是否存在（两个可能的位置）
            repo_dir = CONFIG_DIR / "claude-code-zh-cn-repo"
            info["installed"] = repo_dir.exists() or ZHCN_REPO_DIR.exists()
            return info
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def install_zhcn_repo(self):
        """安装汉化仓库"""
        try:
            # 汉化仓库的实际位置
            repo_dir = CONFIG_DIR / "claude-code-zh-cn-repo"
            
            # 检查是否已安装（检查两个可能的位置）
            if repo_dir.exists():
                return {"ok": True, "msg": "汉化仓库已存在"}
            if ZHCN_REPO_DIR.exists() and (ZHCN_REPO_DIR / "install.ps1").exists():
                return {"ok": True, "msg": "汉化仓库已存在"}
            
            # 创建目录并克隆
            repo_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = f'git clone https://github.com/taekchef/claude-code-zh-cn.git "{repo_dir}"'
            out, err, rc = run_cmd(cmd, timeout=120)
            
            if rc == 0:
                return {"ok": True, "msg": "汉化仓库安装成功"}
            else:
                # 清理失败的目录
                import shutil
                if repo_dir.exists():
                    shutil.rmtree(repo_dir, ignore_errors=True)
                return {"ok": False, "msg": f"安装失败: {err}"}
        except Exception as e:
            return {"ok": False, "msg": f"安装失败: {str(e)}"}
    
    def apply_patch(self):
        """应用汉化补丁（完整流程）"""
        try:
            # 查找安装脚本 - 优先在插件目录找，然后在仓库目录找
            repo_dir = CONFIG_DIR / "claude-code-zh-cn-repo"
            plugin_dir = PLUGINS_DIR / "claude-code-zh-cn"
            
            # 确定安装脚本路径
            install_ps = None
            if repo_dir.exists() and (repo_dir / "install.ps1").exists():
                install_ps = repo_dir / "install.ps1"
            elif plugin_dir.exists() and (plugin_dir / "install.ps1").exists():
                install_ps = plugin_dir / "install.ps1"
                repo_dir = plugin_dir
            
            if not install_ps:
                return {"ok": False, "msg": "未找到汉化仓库，请先安装"}
            
            # 步骤1: 检查 Claude 进程
            if self._is_claude_running():
                return {"ok": False, "msg": "Claude Code 正在运行，请先关闭所有 Claude 窗口后再试", "need_close": True}
            
            # 步骤2: 应用 settings.json 配置
            cfg_result = self._apply_settings_patch()
            
            # 步骤3: 运行安装脚本打二进制补丁
            if PLATFORM == "Windows":
                cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{install_ps}" -SkipBanner'
                out, err, rc = run_cmd(cmd, cwd=str(repo_dir), timeout=120)
                
                if rc == 0:
                    return {"ok": True, "msg": f"补丁已应用！{cfg_result}"}
                else:
                    return {"ok": False, "msg": f"安装脚本执行失败: {err or out}"}
            else:
                # macOS/Linux
                install_sh = repo_dir / "install.sh"
                if install_sh.exists():
                    cmd = f'bash "{install_sh}"'
                    out, err, rc = run_cmd(cmd, cwd=str(repo_dir), timeout=120)
                    if rc == 0:
                        return {"ok": True, "msg": f"补丁已应用！{cfg_result}"}
                    else:
                        return {"ok": False, "msg": f"安装脚本执行失败: {err or out}"}
                else:
                    return {"ok": False, "msg": "未找到安装脚本"}
        except Exception as e:
            return {"ok": False, "msg": f"补丁失败: {str(e)}"}
    
    def _is_claude_running(self):
        """检查 Claude 是否在运行"""
        try:
            if PLATFORM == "Windows":
                out, _, rc = run_cmd('tasklist /FI "IMAGENAME eq claude.exe" /NH', timeout=5)
                return "claude.exe" in out.lower()
            else:
                out, _, rc = run_cmd('pgrep -x claude', timeout=5)
                return rc == 0
        except:
            return False
    
    def _apply_settings_patch(self):
        """应用 settings.json 中的汉化配置"""
        try:
            cfg = load_config()
            
            # 设置语言
            cfg["language"] = "Chinese"
            
            # 设置 spinnerVerbs
            cfg["spinnerVerbs"] = {
                "mode": "replace",
                "verbs": ["思考中", "分析中", "处理中", "生成中", "加载中"]
            }
            
            # 启用插件
            if "enabledPlugins" not in cfg:
                cfg["enabledPlugins"] = {}
            cfg["enabledPlugins"]["claude-code-zh-cn@claude-code-zh-cn"] = True
            
            save_config(cfg)
            return "设置已更新"
        except:
            return "设置更新失败"
    
    def remove_patch(self):
        """移除汉化补丁"""
        try:
            # 检查 Claude 进程
            if self._is_claude_running():
                return {"ok": False, "msg": "Claude Code 正在运行，请先关闭所有 Claude 窗口后再试", "need_close": True}
            
            # 恢复二进制备份
            claude_bin = self._find_claude_binary()
            backup_restored = False
            if claude_bin:
                backup_file = Path(claude_bin + ".zh-cn-backup")
                if backup_file.exists():
                    import shutil
                    try:
                        shutil.copy2(str(backup_file), claude_bin)
                        backup_restored = True
                    except:
                        pass
            
            # 移除 settings 中的汉化配置
            cfg = load_config()
            cfg.pop("language", None)
            cfg.pop("spinnerVerbs", None)
            cfg.pop("spinnerTipsEnabled", None)
            cfg.pop("spinnerTipsOverride", None)
            
            # 禁用插件
            if "enabledPlugins" in cfg:
                cfg["enabledPlugins"]["claude-code-zh-cn@claude-code-zh-cn"] = False
            
            # 删除补丁标记
            marker_file = ZHCN_REPO_DIR / ".patched-version"
            if marker_file.exists():
                marker_file.unlink()
            
            save_config(cfg)
            
            msg = "补丁已移除"
            if backup_restored:
                msg += "，二进制已恢复原始版本"
            return {"ok": True, "msg": msg}
        except Exception as e:
            return {"ok": False, "msg": f"移除失败: {str(e)}"}
    
    def kill_claude(self):
        """关闭所有 Claude 进程"""
        try:
            if PLATFORM == "Windows":
                run_cmd('taskkill /F /IM claude.exe', timeout=10)
            else:
                run_cmd('pkill -x claude', timeout=10)
            time.sleep(1)
            if self._is_claude_running():
                return {"ok": False, "msg": "部分进程未能关闭"}
            return {"ok": True, "msg": "Claude 已关闭"}
        except Exception as e:
            return {"ok": False, "msg": f"关闭失败: {str(e)}"}
    
    def save_claude_path(self, path):
        """保存 Claude Code 安装路径"""
        try:
            if not path:
                return {"ok": False, "msg": "路径不能为空"}
            
            path = path.strip().strip('"').strip("'")
            if not Path(path).exists():
                return {"ok": False, "msg": f"路径不存在: {path}"}
            
            cfg = load_config()
            cfg["claude_install_path"] = path
            save_config(cfg)
            return {"ok": True, "msg": "路径已保存"}
        except Exception as e:
            return {"ok": False, "msg": f"保存失败: {str(e)}"}
    
    def get_claude_path(self):
        """获取当前 Claude 安装路径"""
        try:
            cfg = load_config()
            custom_path = cfg.get("claude_install_path", "")
            detected_path = self._find_claude_binary()
            return {
                "ok": True,
                "custom_path": custom_path,
                "detected_path": detected_path or "",
            }
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def toggle_zhcn_plugin(self, enable):
        """启用/禁用汉化插件"""
        try:
            cfg = load_config()
            
            if "enabledPlugins" not in cfg:
                cfg["enabledPlugins"] = {}
            
            cfg["enabledPlugins"]["claude-code-zh-cn@claude-code-zh-cn"] = enable
            
            if save_config(cfg):
                status = "启用" if enable else "禁用"
                return {"ok": True, "msg": f"插件已{status}"}
            return {"ok": False, "msg": "操作失败"}
        except Exception as e:
            return {"ok": False, "msg": f"操作失败: {str(e)}"}
    
    # ---- 配置管理 ----
    
    def get_full_config(self):
        """获取完整配置"""
        try:
            cfg = load_config()
            return {"ok": True, "config": cfg}
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def save_full_config(self, config_json):
        """保存完整配置"""
        try:
            cfg = json.loads(config_json)
            if save_config(cfg):
                return {"ok": True, "msg": "配置已保存"}
            return {"ok": False, "msg": "保存失败"}
        except json.JSONDecodeError as e:
            return {"ok": False, "msg": f"JSON 格式错误: {str(e)}"}
        except Exception as e:
            return {"ok": False, "msg": f"保存失败: {str(e)}"}
    
    def get_env_vars(self):
        """获取环境变量配置"""
        try:
            cfg = load_config()
            env_vars = {}
            for key, value in cfg.items():
                if key.startswith("ANTHROPIC_"):
                    env_vars[key] = value
            return {"ok": True, "env_vars": env_vars}
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def save_env_vars(self, env_vars):
        """保存环境变量配置"""
        try:
            cfg = load_config()
            for key, value in env_vars.items():
                cfg[key] = value
            if save_config(cfg):
                return {"ok": True, "msg": "环境变量已保存"}
            return {"ok": False, "msg": "保存失败"}
        except Exception as e:
            return {"ok": False, "msg": f"保存失败: {str(e)}"}
    
    def get_permissions(self):
        """获取权限规则"""
        try:
            cfg = load_config()
            permissions = cfg.get("permissions", {})
            return {"ok": True, "permissions": permissions}
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def save_permissions(self, permissions):
        """保存权限规则"""
        try:
            cfg = load_config()
            cfg["permissions"] = permissions
            if save_config(cfg):
                return {"ok": True, "msg": "权限规则已保存"}
            return {"ok": False, "msg": "保存失败"}
        except Exception as e:
            return {"ok": False, "msg": f"保存失败: {str(e)}"}
    
    # ---- 工具 ----
    
    def open_claude(self, work_dir=None):
        """打开 Claude Code"""
        try:
            if work_dir:
                # 从指定工作目录打开
                if PLATFORM == "Windows":
                    # 使用start命令在新窗口中打开，设置工作目录
                    cmd = f'start "Claude Code" /D "{work_dir}" claude'
                    subprocess.Popen(cmd, shell=True)
                elif PLATFORM == "Darwin":
                    subprocess.Popen(['open', '-a', 'Terminal', '--', 'bash', '-c', f'cd {work_dir} && claude'])
                else:
                    subprocess.Popen(['x-terminal-emulator', '-e', f'bash -c "cd {work_dir} && claude"'])
            else:
                # 直接打开
                if PLATFORM == "Windows":
                    subprocess.Popen('start "Claude Code" claude', shell=True)
                elif PLATFORM == "Darwin":
                    subprocess.Popen(['open', '-a', 'Terminal', '--', 'claude'])
                else:
                    subprocess.Popen(['x-terminal-emulator', '-e', 'claude'])
            return {"ok": True, "msg": "已启动 Claude Code"}
        except Exception as e:
            return {"ok": False, "msg": f"启动失败: {str(e)}"}
    
    def save_work_folder(self, folder, name=None, group="默认"):
        """保存常用工作文件夹"""
        try:
            cfg = load_config()
            work_folders = cfg.get("work_folders", {})
            
            if group not in work_folders:
                work_folders[group] = []
            
            # 检查是否已存在
            for item in work_folders[group]:
                if isinstance(item, dict) and item.get("path") == folder:
                    return {"ok": True, "msg": "文件夹已存在"}
            
            # 使用自定义名称或文件夹名作为名称
            if not name:
                name = os.path.basename(folder)
            
            work_folders[group].append({
                "name": name,
                "path": folder
            })
            cfg["work_folders"] = work_folders
            save_config(cfg)
            return {"ok": True, "msg": "已保存"}
        except Exception as e:
            return {"ok": False, "msg": f"保存失败: {str(e)}"}
    
    def get_work_folders(self):
        """获取常用工作文件夹"""
        try:
            cfg = load_config()
            return {
                "ok": True, 
                "folders": cfg.get("work_folders", {}),
                "last_selected": cfg.get("last_selected_folder", "")
            }
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def save_last_selected_folder(self, folder):
        """保存最后选择的工作文件夹"""
        try:
            cfg = load_config()
            cfg["last_selected_folder"] = folder
            save_config(cfg)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def create_group(self, group_name):
        """创建空分组"""
        try:
            cfg = load_config()
            work_folders = cfg.get("work_folders", {})
            
            if group_name not in work_folders:
                work_folders[group_name] = []
                cfg["work_folders"] = work_folders
                save_config(cfg)
            return {"ok": True, "msg": "分组已创建"}
        except Exception as e:
            return {"ok": False, "msg": f"创建失败: {str(e)}"}
    
    def delete_work_folder(self, folder_path, group="默认"):
        """删除工作文件夹"""
        try:
            cfg = load_config()
            work_folders = cfg.get("work_folders", {})
            
            if group in work_folders:
                work_folders[group] = [
                    item for item in work_folders[group]
                    if not (isinstance(item, dict) and item.get("path") == folder_path)
                ]
                if not work_folders[group]:
                    del work_folders[group]
                cfg["work_folders"] = work_folders
                save_config(cfg)
            return {"ok": True, "msg": "已删除"}
        except Exception as e:
            return {"ok": False, "msg": f"删除失败: {str(e)}"}
    
    def rename_work_folder_group(self, old_name, new_name):
        """重命名工作文件夹分组"""
        try:
            cfg = load_config()
            work_folders = cfg.get("work_folders", {})
            
            if old_name in work_folders:
                work_folders[new_name] = work_folders.pop(old_name)
                cfg["work_folders"] = work_folders
                save_config(cfg)
            return {"ok": True, "msg": "已重命名"}
        except Exception as e:
            return {"ok": False, "msg": f"重命名失败: {str(e)}"}
    
    def delete_group(self, group_name):
        """删除工作文件夹分组"""
        try:
            cfg = load_config()
            work_folders = cfg.get("work_folders", {})
            
            if group_name in work_folders:
                del work_folders[group_name]
                cfg["work_folders"] = work_folders
                save_config(cfg)
            return {"ok": True, "msg": "分组已删除"}
        except Exception as e:
            return {"ok": False, "msg": f"删除失败: {str(e)}"}
    
    def rename_work_folder(self, folder_path, new_name, group="默认"):
        """重命名工作文件夹"""
        try:
            cfg = load_config()
            work_folders = cfg.get("work_folders", {})
            
            if group in work_folders:
                for item in work_folders[group]:
                    if isinstance(item, dict) and item.get("path") == folder_path:
                        item["name"] = new_name
                        break
                cfg["work_folders"] = work_folders
                save_config(cfg)
            return {"ok": True, "msg": "已重命名"}
        except Exception as e:
            return {"ok": False, "msg": f"重命名失败: {str(e)}"}
    
    def select_folder_dialog(self):
        """打开文件夹选择对话框"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            folder = filedialog.askdirectory(title="选择工作文件夹")
            root.destroy()
            
            if folder:
                return {"ok": True, "folder": folder}
            return {"ok": False, "msg": "未选择文件夹"}
        except Exception as e:
            return {"ok": False, "msg": f"选择失败: {str(e)}"}
    
    def open_config_folder(self):
        """打开配置文件夹"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            if PLATFORM == "Windows":
                os.startfile(str(CONFIG_DIR))
            elif PLATFORM == "Darwin":
                run_cmd(f'open "{CONFIG_DIR}"')
            else:
                run_cmd(f'xdg-open "{CONFIG_DIR}"')
            return {"ok": True, "msg": "已打开配置文件夹"}
        except Exception as e:
            return {"ok": False, "msg": f"打开失败: {str(e)}"}
    
    def open_url(self, url):
        """打开 URL"""
        try:
            webbrowser.open(url)
            return {"ok": True}
        except:
            return {"ok": False}

# ============================================================
#  启动
# ============================================================

def set_window_icon(window):
    """设置窗口图标"""
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if not os.path.exists(icon_path):
            # 如果没有ico文件，尝试使用png
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        
        if os.path.exists(icon_path):
            if PLATFORM == "Windows":
                import ctypes
                time.sleep(1.5)

                hwnd = None
                if hasattr(window, "native_handle") and window.native_handle:
                    hwnd = window.native_handle
                elif hasattr(window, "_hwnd"):
                    hwnd = window._hwnd
                else:
                    EnumWindows = ctypes.windll.user32.EnumWindows
                    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
                    GetWindowText = ctypes.windll.user32.GetWindowTextW
                    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW

                    result = []

                    def enum_cb(hwnd_win, _):
                        length = GetWindowTextLength(hwnd_win)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            GetWindowText(hwnd_win, buff, length + 1)
                            if "Claude" in buff.value:
                                result.append(hwnd_win)
                        return True

                    EnumWindows(EnumWindowsProc(enum_cb), 0)
                    if result:
                        hwnd = result[0]

                if hwnd:
                    WM_SETICON = 0x0080
                    IMAGE_ICON = 1
                    LR_LOADFROMFILE = 0x0010
                    icon = ctypes.windll.user32.LoadImageW(0, icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                    if icon:
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 0, icon)
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 1, icon)
    except Exception as e:
        print(f"设置图标失败: {e}")

def get_resource_path(relative_path):
    """获取资源文件路径"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def main():
    # 隐藏控制台窗口
    if PLATFORM == "Windows":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    bridge = ApiBridge()
    ui_dir = get_resource_path("ui")
    html_path = os.path.join(ui_dir, "index.html")
    
    if not os.path.exists(html_path):
        print(f"错误: 找不到 UI 文件: {html_path}")
        sys.exit(1)
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    window = webview.create_window(
        title="Claude Code 管理工具",
        html=html,
        js_api=bridge,
        width=1100,
        height=720,
        min_size=(900, 600),
        resizable=True,
        text_select=True,
    )
    
    webview.start(set_window_icon, window, debug=False)

if __name__ == "__main__":
    main()