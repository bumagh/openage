# OpenAge VPS 部署经验（供 AI Code 参考）

## 实际部署环境

| 项目 | 值 |
|------|-----|
| 服务器 | 腾讯云 Debian 12 |
| IP | 101.43.115.124 |
| SSH 端口 | 22 |
| 域名 | app.tutlab.tech |
| 部署路径 | `/www/wwwroot/app.tutlab.tech/public/age/` |
| 虚拟环境 | `/www/wwwroot/app.tutlab.tech/public/age/venv/` |
| 服务端口 | **8001**（不是 8000） |
| Nginx 子路径 | `/age`（`--root-path /age`） |
| systemd 服务名 | `openage` |

> ⚠️ `deploy/deploy.sh` 和 `deploy/openage.service` 中写的是 `/opt/openage` + 端口 8000，**与实际不符**，勿直接使用。

---

## systemd 服务实际配置

```ini
# /etc/systemd/system/openage.service
[Service]
WorkingDirectory=/www/wwwroot/app.tutlab.tech/public/age
ExecStart=/www/wwwroot/app.tutlab.tech/public/age/venv/bin/uvicorn \
    app.main:app --host 127.0.0.1 --port 8001 --root-path /age
```

---

## 常用运维命令

```bash
# 上传单个文件
scp -P 22 app/main.py root@101.43.115.124:/www/wwwroot/app.tutlab.tech/public/age/app/main.py
scp -P 22 app/static/index.html root@101.43.115.124:/www/wwwroot/app.tutlab.tech/public/age/app/static/index.html

# 重启服务
ssh root@101.43.115.124 "systemctl restart openage"

# 查看服务状态
ssh root@101.43.115.124 "systemctl status openage --no-pager"

# 查看日志（排查启动失败）
ssh root@101.43.115.124 "journalctl -u openage -n 50 --no-pager"

# 验证服务是否正常
ssh root@101.43.115.124 "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8001/"
```

---

## 历史 Bug 记录

### Bug 1：502 Bad Gateway
- **原因**：`app/main.py` 中 `ChatMessage` 类定义缺失（只有属性，没有 `class ChatMessage(BaseModel):` 这行），导致 `NameError`，uvicorn 启动失败。
- **排查方法**：`journalctl -u openage -n 30` 查看具体报错行号。
- **修复**：补全类定义后上传，重启服务即可。

### Bug 2：页面底部显示多余 JS 代码
- **原因**：`index.html` 中 `</script>` 标签后面意外残留了一大段重复的 JS 函数（约 200 行），浏览器将其作为文本渲染在页面底部。
- **修复**：删除 `</script>` 之后的所有重复函数代码。

### Bug 3：未生成报告可直接发送对话
- **原因**：`sendChat()` 没有检查 `reportContext` 是否为 null。
- **修复**：在 `sendChat()` 开头加判断，`reportContext` 为空时提示用户先完成预测。

---

## 部署流程（快速参考）

1. 本地修改代码
2. `scp` 上传变更文件到 `/www/wwwroot/app.tutlab.tech/public/age/`
3. `systemctl restart openage`
4. `curl http://127.0.0.1:8001/` 验证返回 200
5. 浏览器访问 `http://app.tutlab.tech/age/` 确认页面正常
