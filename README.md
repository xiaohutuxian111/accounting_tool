# accounting_tool 项目文档

## 1. 项目概述

`accounting_tool` 是一个基于 Python 3.11 的本地桌面会计工具项目，当前已经完成并接通的核心功能是 `发票识别`。

当前技术路线：

- GUI：`PySide6` + `PySide6-Fluent-Widgets`
- OCR：`PaddleOCR`
- 配置：`PyYAML`
- 日志：`loguru`
- 数据存储：`SQLite`

当前产品形态不是单纯的 OCR Demo，而是一个按会计工具方向演进的桌面应用基础骨架。现阶段已经完成：

- Fluent 风格主窗口
- 发票图片识别
- OCR 结果解析与校验
- 识别结果导出 JSON
- 识别结果保存到本地台账数据库
- 参数设置即时生效


## 2. 当前功能范围

当前已落地功能：

- `发票识别`
  - 选择图片
  - 执行 OCR
  - 展示识别字段
  - 展示原始文本
  - 导出 JSON
  - 保存到台账

- `参数设置`
  - 识别引擎
  - 识别语言
  - GPU 开关
  - 调试图保存开关
  - 导出目录 / 调试目录 / 临时目录
  - 日志级别
  - 主题
  - 主题色
  - 记住窗口大小

当前未开发页面：

- 发票台账
- 统计分析
- 税务工具

这些模块目前不执行页面开发，但项目结构已经为后续扩展预留了方向。


## 3. 目录结构

当前推荐关注的主目录如下：

```text
accounting_tool/
  config/
    config.yaml                 # 主配置文件

  data/
    db/
      accounting.db             # SQLite 数据库
    debug/                      # OCR 调试图片
    export/                     # JSON 导出目录
    temp/                       # 临时目录

  logs/
    app.log                     # 应用日志

  app/
    main.py                     # 程序入口
    bootstrap.py                # 启动初始化
    cli.py                      # CLI 参数定义

    core/
      config.py                 # 配置加载与保存
      logging.py                # 日志初始化

    db/
      sqlite_manager.py         # SQLite 管理器

    gui/
      app_window.py             # Fluent 主窗口
      components/
        fluent_setting_cards.py # 自定义设置卡片
      pages/
        settings_page.py        # 设置页

    modules/
      invoice/
        application/
          dto.py
          invoice_ocr_service.py
          invoice_ledger_service.py
        domain/
          entities.py
          invoice_parser.py
          validator.py
        infrastructure/
          image_preprocess.py
          invoice_repo.py
          ocr_engine.py
        ui/
          invoice_ocr_page.py
          invoice_ocr_worker.py
```


## 4. 架构说明

项目已经从早期的“按技术层分散目录”收敛为“按业务模块组织”的结构。当前发票功能采用四层组织：

### 4.1 application

负责业务流程编排，不直接处理界面展示。

- `invoice_ocr_service.py`
  - 编排预处理、OCR、解析、校验
- `invoice_ledger_service.py`
  - 编排识别结果入库
- `dto.py`
  - 定义 `InvoiceOCRResult`

### 4.2 domain

负责业务规则和领域对象。

- `entities.py`
  - 发票实体 `InvoiceRecord`
- `invoice_parser.py`
  - OCR 文本转发票字段
- `validator.py`
  - 发票识别结果校验

### 4.3 infrastructure

负责与具体技术实现打交道。

- `ocr_engine.py`
  - PaddleOCR 封装
- `image_preprocess.py`
  - 图像预处理
- `invoice_repo.py`
  - SQLite 仓储实现

### 4.4 ui

负责界面与线程调度。

- `invoice_ocr_page.py`
  - 发票识别页面
- `invoice_ocr_worker.py`
  - OCR 异步工作线程


## 5. 运行流程

### 5.1 GUI 启动流程

入口文件：`app/main.py`

执行过程：

1. 解析命令行参数
2. 调用 `bootstrap()` 初始化配置、目录、日志、数据库
3. 创建 `QApplication`
4. 应用主题与主题色
5. 创建 `AppWindow`
6. 加载 `发票识别` 和 `设置` 页面

### 5.2 发票识别流程

`InvoiceOCRPage -> InvoiceOCRWorker -> InvoiceOCRService`

执行链路：

1. 读取图片
2. 图像预处理
3. 调用 PaddleOCR
4. 解析 OCR 文本
5. 校验字段结果
6. 返回 `InvoiceOCRResult`
7. GUI 展示结果
8. 可选导出 JSON 或保存到台账

### 5.3 保存台账流程

`InvoiceOCRPage -> InvoiceLedgerService -> InvoiceRepository -> SQLite`

执行链路：

1. 接收识别结果 DTO
2. 判断发票代码 + 发票号码是否重复
3. 转换为 `InvoiceRecord`
4. 写入 `invoices` 表


## 6. 配置说明

主配置文件位于：

- [config/config.yaml](/C:/Users/stone/PycharmProjects/accounting_tool/config/config.yaml)

当前主要配置项：

```yaml
app:
  name: 发票识别助手
  theme: dark
  theme_color: "#2dd36f"
  language: zh-CN
  remember_window_size: true
  window_width: 1050
  window_height: 800

ocr:
  engine: paddleocr
  lang: ch
  use_gpu: false
  save_debug_image: true

storage:
  db_path: data/db/accounting.db
  export_dir: data/export
  debug_dir: data/debug
  temp_dir: data/temp

log:
  level: INFO
  dir: logs
```

配置优先级：

`默认配置 < config/config.yaml < 环境变量 < CLI 参数`


## 7. 数据存储

当前数据库为：

- `data/db/accounting.db`

当前核心表：

- `invoices`

主要字段包括：

- 发票类型
- 发票代码
- 发票号码
- 开票日期
- 购买方
- 销售方
- 不含税金额
- 税额
- 价税合计
- 校验码
- 置信度
- 校验状态
- 源文件路径
- 原始 OCR 文本
- 创建时间


## 8. 开发与运行

### 8.1 启动 GUI

```bash
uv run python -m app.main
```

### 8.2 命令行执行 OCR

```bash
uv run python -m app.main invoice-ocr <图片路径>
```

### 8.3 基础编译检查

```bash
python -m compileall app
```


## 9. 当前限制

当前已知限制如下：

- `PaddleOCR` 首次运行依赖模型下载或本地模型目录
- 在当前环境中，如果网络不可用，OCR 真实识别可能无法完成
- `发票台账 / 统计分析 / 税务工具` 页面尚未开发
- 项目已经完成结构整理，但自动化测试仍未补齐


## 10. 后续扩展约定

为避免后续继续把代码写散，新增业务模块建议统一按下面方式组织：

```text
app/modules/<module_name>/
  application/
  domain/
  infrastructure/
  ui/
```

例如后续如果补：

- `invoice/ui/invoice_ledger_page.py`
- `analytics/...`
- `tax/...`

都应遵循同样的模块边界。

约定如下：

- UI 只负责展示、交互和线程调度
- application 负责流程编排
- domain 负责规则和实体
- infrastructure 负责数据库、OCR、第三方集成
- 尽量不要让页面直接依赖裸 `dict`
- 新增功能优先定义 DTO 或实体对象


## 11. 维护建议

后续建议按这个顺序继续推进：

1. 补 `发票台账` 页面，但沿用当前 `modules/invoice` 结构
2. 给 `invoice_parser / validator / repo / config` 补最小测试
3. 把 PaddleOCR 本地模型路径做成明确配置项
4. 再考虑接入新的业务模块


## 12. 文档说明

本文件已从早期“项目分析报告”调整为“项目文档”，后续应持续维护为：

- 项目结构说明
- 模块职责说明
- 运行说明
- 配置说明
- 扩展约定

而不是一次性的分析结论记录。

## 13. 附加文档

- [Git 操作说明](docs/GIT_GUIDE.md)
