# 晋江、长佩纯爱跨媒介行业调查

一次性调查，窗口 2024-01-01 至北京时间 2026-11-10。覆盖目标是两站全部符合原发或作品签约、平台纯爱分类条件的作品；试采不替代全量。实体出版排除，电子书保留。不制作采购排名。

当前为部分完成。候选来源记录、确认作品、商业产品、事件和指标分别统计；未知总体不报告全站覆盖率。

## 使用

Python 3，依赖 requests、beautifulsoup4。`python src/research.py export` 重算本地导出，`python -m unittest discover -s tests -v` 执行模拟测试，`python src/research.py backup` 生成带校验清单的本地快照。

飞书使用本机 `lark-cli` 用户登录，通过私有 `config/feishu.local.json` 定位本项目独立 Base。`python src/feishu_sync.py plan` 预览；`sync` 逐批 dry-run、写入并完整回读。相同记录跳过；差异记录停止等待具体差异审查，不盲目覆盖。不要复制其他项目凭据。

GitHub 只保存代码、PRD、规则、测试和清理后的阶段状态。数据库、证据、部署配置、回执、完整研究数据及恢复包均不上传。仅有代码仓库不能恢复数据。

参阅 [状态](docs/STATUS.md)、[字段与统计口径](docs/DATA_DICTIONARY.md)、[接续说明](docs/RESUME.md)。
