"""
Regists CMS Server
轻量内容管理系统，管理"最新动态"页面内容。
用法: python admin/server.py [port]
默认端口 8001，访问 http://localhost:8001/admin/
"""

import http.server
import json
import os
import re
import sys
import urllib.parse
import mimetypes

# ----- 路径配置 -----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATA_JS = os.path.join(DATA_DIR, 'data.js')
UPDATES_JSON = os.path.join(DATA_DIR, 'updates.json')

# ----- 数据操作 -----
def extract_updates_from_js(content):
    """从 data.js 中提取 updates JSON 对象"""
    start_marker = 'updates:'
    end_marker = 'regionData:'
    start = content.find(start_marker)
    end = content.find(end_marker)
    if start == -1 or end == -1:
        return None
    brace_start = content.find('{', start)
    if brace_start == -1 or brace_start > end:
        return None
    depth = 0
    json_end = -1
    for i in range(brace_start, end):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                json_end = i + 1
                break
    if json_end == -1:
        return None
    return json.loads(content[brace_start:json_end])


def init_updates_json():
    if os.path.exists(UPDATES_JSON):
        return
    try:
        with open(DATA_JS, 'r', encoding='utf-8') as f:
            content = f.read()
        updates_data = extract_updates_from_js(content)
        if updates_data:
            with open(UPDATES_JSON, 'w', encoding='utf-8') as f:
                json.dump(updates_data, f, ensure_ascii=False, indent=2)
            print(f"[CMS] 从 data.js 导入 {len(updates_data.get('updates', []))} 条更新")
            return
    except Exception as e:
        print(f"[CMS] 导入警告: {e}")
    with open(UPDATES_JSON, 'w', encoding='utf-8') as f:
        json.dump({"updates": []}, f, ensure_ascii=False, indent=2)


def read_updates():
    with open(UPDATES_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_updates(data):
    with open(UPDATES_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    sync_to_data_js(data)


def sync_to_data_js(updates_data):
    with open(DATA_JS, 'r', encoding='utf-8') as f:
        content = f.read()
    start_marker = 'updates:'
    end_marker = 'regionData:'
    start = content.find(start_marker)
    end = content.find(end_marker)
    if start == -1 or end == -1:
        print("[CMS] ⚠️  data.js 中找不到标记")
        return False
    brace_start = content.find('{', start)
    if brace_start == -1 or brace_start > end:
        return False
    depth = 0
    json_end = -1
    for i in range(brace_start, end):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                json_end = i + 1
                break
    if json_end == -1:
        return False
    new_json_str = json.dumps(updates_data, ensure_ascii=False)
    new_content = content[:brace_start] + new_json_str + content[json_end:]
    if new_content == content:
        return True
    with open(DATA_JS, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"[CMS] ✅ data.js 已同步 ({len(updates_data.get('updates', []))} 条)")
    return True


# ----- MIME 类型 -----
MIME_MAP = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.txt': 'text/plain; charset=utf-8',
    '.xml': 'application/xml; charset=utf-8',
}


def guess_mime(path):
    ext = os.path.splitext(path)[1].lower()
    return MIME_MAP.get(ext, 'application/octet-stream')


# ----- 请求处理 -----
class CMSHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stderr.write(f"[CMS] {args[0]} {args[1]} {args[2]}\n")

    def _send_file(self, filepath):
        """读取并发送静态文件"""
        filepath = os.path.normpath(filepath)
        # 安全检查：防止目录穿越
        if not filepath.startswith(os.path.normpath(BASE_DIR)):
            self.send_error(403)
            return
        if not os.path.isfile(filepath):
            self.send_error(404)
            return
        mime = guess_mime(filepath)
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, str(e))

    def _serve_static(self, path):
        """服务静态文件"""
        # 默认首页
        if path == '/' or path == '':
            path = '/index.html'
        # /admin/ → /admin/index.html
        if path == '/admin/' or path == '/admin':
            path = '/admin/index.html'
        filepath = os.path.join(BASE_DIR, path.lstrip('/'))
        self._send_file(filepath)

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        return json.loads(raw)

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    # ----- HTTP Methods -----
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/updates':
            try:
                data = read_updates()
                self._json_response(data)
            except Exception as e:
                self._json_response({'error': str(e)}, 500)
            return
        self._serve_static(parsed.path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            if parsed.path == '/api/updates':
                body = self._read_body()
                data = read_updates()
                updates = data['updates']
                # 生成 ID
                if not body.get('id'):
                    existing_ids = {u['id'] for u in updates}
                    n = 1
                    while f'{n:03d}' in existing_ids:
                        n += 1
                    body['id'] = f'{n:03d}'
                # 校验
                for field in ['title', 'date', 'category', 'summary']:
                    if field not in body or not body[field]:
                        self._json_response({'error': f'缺少必填字段: {field}'}, 400)
                        return
                new_item = {
                    'id': body['id'],
                    'title': body['title'],
                    'date': body['date'],
                    'category': body['category'],
                    'summary': body['summary'],
                    'tags': body.get('tags', []),
                }
                if body.get('sourceUrl'):
                    new_item['sourceUrl'] = body['sourceUrl']
                updates.append(new_item)
                write_updates(data)
                self._json_response(new_item, 201)
                return
            if parsed.path == '/api/publish':
                data = read_updates()
                sync_to_data_js(data)
                self._json_response({'status': 'ok', 'count': len(data['updates'])})
                return
            self._json_response({'error': 'Not Found'}, 404)
        except Exception as e:
            self._json_response({'error': str(e)}, 500)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            match = re.match(r'/api/updates/(\d+)', parsed.path)
            if match:
                item_id = match.group(1)
                body = self._read_body()
                data = read_updates()
                for item in data['updates']:
                    if item['id'] == item_id:
                        item['title'] = body.get('title', item['title'])
                        item['date'] = body.get('date', item['date'])
                        item['category'] = body.get('category', item['category'])
                        item['summary'] = body.get('summary', item['summary'])
                        item['tags'] = body.get('tags', item.get('tags', []))
                        if 'sourceUrl' in body:
                            item['sourceUrl'] = body['sourceUrl']
                        elif 'sourceUrl' in item:
                            del item['sourceUrl']
                        write_updates(data)
                        self._json_response(item)
                        return
                self._json_response({'error': 'Not Found'}, 404)
                return
            self._json_response({'error': 'Not Found'}, 404)
        except Exception as e:
            self._json_response({'error': str(e)}, 500)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            match = re.match(r'/api/updates/(\d+)', parsed.path)
            if match:
                item_id = match.group(1)
                data = read_updates()
                for i, item in enumerate(data['updates']):
                    if item['id'] == item_id:
                        data['updates'].pop(i)
                        write_updates(data)
                        self._json_response({'deleted': item_id})
                        return
                self._json_response({'error': 'Not Found'}, 404)
                return
            self._json_response({'error': 'Not Found'}, 404)
        except Exception as e:
            self._json_response({'error': str(e)}, 500)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


# ----- 启动 -----
if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    init_updates_json()
    server = http.server.HTTPServer(('127.0.0.1', port), CMSHandler)
    print(f"\n  🚀 Regists CMS 服务已启动")
    print(f"  📝 管理后台: http://localhost:{port}/admin/")
    print(f"  🌐 站点预览: http://localhost:{port}/index.html")
    print(f"  ⏹  按 Ctrl+C 停止\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  [CMS] 服务已停止")
        server.server_close()
