# Git 操作说明

本文档说明 `accounting_tool` 仓库的常见 Git 操作，适用于日常开发、提交和协作。

## 1. 开始前

进入项目目录：

```powershell
cd C:\Users\stone\PycharmProjects\accounting_tool
```

先检查当前状态：

```powershell
git status
```

建议在提交前重点确认以下内容是否误加入版本控制：

- `.venv/`
- `data/`
- `logs/`
- `build/`
- `dist/`
- `.idea/`

如果这些目录出现在 `git status` 中，先确认是不是你确实要提交的内容。

## 2. 拉取最新代码

查看当前分支：

```powershell
git branch --show-current
```

拉取远端最新代码：

```powershell
git pull
```

如果你希望先看差异再决定是否处理冲突，可以先执行：

```powershell
git fetch
git status
git log --oneline --decorate --graph HEAD..origin/当前分支名
```

## 3. 新功能开发流程

建议每个需求或修复都使用独立分支。

从当前分支创建新分支：

```powershell
git checkout -b feature/update-readme
```

开发完成后查看改动：

```powershell
git status
git diff
```

只暂存需要提交的文件：

```powershell
git add README.md docs/GIT_GUIDE.md
```

提交：

```powershell
git commit -m "docs: add git operation guide"
```

推送到远端：

```powershell
git push -u origin feature/update-readme
```

## 4. 常用查看命令

查看简洁提交历史：

```powershell
git log --oneline --decorate --graph -20
```

查看某个文件的修改：

```powershell
git diff -- README.md
```

查看已暂存但未提交的内容：

```powershell
git diff --cached
```

查看某次提交详情：

```powershell
git show <commit-id>
```

## 5. 撤销与修正

取消暂存某个文件：

```powershell
git restore --staged README.md
```

丢弃某个文件的工作区修改：

```powershell
git restore README.md
```

注意：`git restore` 会直接丢弃未提交修改，执行前先确认。

如果只是想修正最近一次提交说明，但不改提交内容：

```powershell
git commit --amend -m "docs: refine git guide"
```

## 6. 处理冲突

执行 `git pull` 或分支合并后，如果出现冲突：

1. 运行 `git status` 查看冲突文件。
2. 打开冲突文件，处理 `<<<<<<<`、`=======`、`>>>>>>>` 标记。
3. 保存后重新暂存文件。
4. 提交冲突解决结果。

常用命令：

```powershell
git status
git add <冲突文件>
git commit
```

## 7. 文档类改动提交流程

如果本次只是更新文档，建议按下面顺序执行：

```powershell
git status
git diff -- README.md
git diff -- docs/GIT_GUIDE.md
git add README.md docs/GIT_GUIDE.md
git commit -m "docs: update project documentation"
```

## 8. 提交信息建议

推荐使用简洁前缀，便于后续查看历史：

- `docs:` 文档修改
- `feat:` 新功能
- `fix:` 缺陷修复
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 杂项维护

示例：

```text
docs: add git operation guide
feat: support pdf invoice extraction
fix: handle empty pdf page error
```

## 9. 这个项目的提交注意事项

- 配置文件改动前，确认是否包含仅本机可用的路径或个人偏好。
- 数据库文件、日志文件、导出文件通常不应提交。
- 提交前优先用 `git diff` 检查是否误带临时调试修改。
- 如果同时改了代码和文档，建议在提交说明里明确范围。

## 10. 推荐的最小日常流程

```powershell
git pull
git checkout -b feature/your-change
git status
git add <需要提交的文件>
git commit -m "feat: describe your change"
git push -u origin feature/your-change
```

## 11. 提交一个版本

如果这次提交对应一个可发布版本，建议把版本号修改、代码提交和 Git 标签一起完成。

先修改项目版本号，例如更新 [pyproject.toml](/C:/Users/stone/PycharmProjects/accounting_tool/pyproject.toml) 中的：

```toml
version = "0.1.0"
```

改完后检查差异：

```powershell
git status
git diff -- pyproject.toml
```

提交版本相关改动：

```powershell
git add pyproject.toml README.md docs/GIT_GUIDE.md
git commit -m "chore: release v0.1.1"
```

为这次提交打标签：

```powershell
git tag -a v0.1.1 -m "release v0.1.1"
```

推送分支和标签：

```powershell
git push
git push origin v0.1.1
```

如果希望一次推送全部本地标签，也可以使用：

```powershell
git push --tags
```

发布前建议至少确认以下几点：

- 版本号已经同步更新。
- 文档和主要功能改动已经提交。
- `git status` 结果干净，避免把半成品一起打进版本标签。

查看当前已有标签：

```powershell
git tag
```

查看某个版本标签对应的内容：

```powershell
git show v0.1.1
```
