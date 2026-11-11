# 晋江、长佩纯爱跨媒介行业调查

一次性调查，窗口 2024-01-01 至北京时间 2026-11-10。覆盖目标是两站全部符合原发或作品签约、平台纯爱分类条件的作品；试采不替代全量。实体出版排除，电子书保留。不制作采购排名。

当前为部分完成。候选来源记录、确认作品、商业产品、事件和指标分别统计；未知总体不报告全站覆盖率。

当前PRD为V1.1（保留原文件名）。主线是窗口内已售出/已授权签约的衍生权利；上线和表现另列，不能用上线日期证明售出年份。`rights_records`保存权利披露，未知独立合同关系不将多行当多笔交易；无日期和跨截止日记录单列。

## 使用

Python 3，依赖 requests、beautifulsoup4。`python src/research.py export` 重算本地导出，`python -m unittest discover -s tests -v` 执行模拟测试，`python src/research.py backup` 生成带校验清单的本地快照。

`python src/analyze_rights_sales.py` 重算售出披露与作品资格分层，并输出私有 `exports/rights-sales-report.md`。`python src/feishu_rights_table.py` 仅建立授权签约表及关联字段；之后必须增量同步并完整回读，建表本身不是交付完成。

飞书使用本机 `lark-cli` 用户登录，通过私有 `config/feishu.local.json` 定位本项目独立 Base。`python src/feishu_sync.py plan` 预览；已有 Base 的续批运行 `python src/feishu_incremental.py --run 唯一批次名`，保存差异、dry-run、写入并完整分页回读。相同记录跳过；远端改动与上次回读基线冲突时停止，不盲目覆盖。不要复制其他项目凭据。

GitHub 只保存代码、PRD、规则、测试和清理后的阶段状态。数据库、证据、部署配置、回执、完整研究数据及恢复包均不上传。仅有代码仓库不能恢复数据。

参阅 [状态](docs/STATUS.md)、[字段与统计口径](docs/DATA_DICTIONARY.md)、[接续说明](docs/RESUME.md)。
