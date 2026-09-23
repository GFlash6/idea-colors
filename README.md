# idea-colors

Idea Ops 的核心代码、可编辑画布、命令行后端与测试。

## 运行

需要 Python 3.10+。在仓库根目录执行：

```powershell
python idea-ops/scripts/idea_ops.py --root . serve
```

命令会在本机启动服务并打开浏览器。项目数据保存在 `.ideas/ideas.json`。

## 验证

```powershell
python .workbuddy/check_graph_mutations.py
node .workbuddy/check-canvas.cjs
node idea-ops/scripts/test_offline.cjs
```

主要目录：

- `idea-ops/assets/`：前端画布与离线交接逻辑
- `idea-ops/scripts/`：数据模型、CLI 和本地 HTTP 服务
- `.workbuddy/`：核心行为回归测试

`.ideas/` 等本地工作区数据默认被忽略，不会提交到仓库。
