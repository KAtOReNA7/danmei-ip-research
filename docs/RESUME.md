# 接续

1. 阅读 PRD、AGENTS、STATUS、私有 exports/coverage_summary.json 和 receipts/validation.json。
2. 确认当前目录是独立项目。不要使用 ebook 配置、凭据或工作流。只有一个写入端。
3. 在新设备拉代码后，单独恢复匹配的数据快照；对 ZIP 内 manifest.json 逐文件校验 SHA256；恢复 SQLite 后跑 integrity_check 和 foreign_key_check。
4. 各设备独立登录 lark-cli，用户已指定飞书只用 CLI。真实 Base 配置不从Git推断；使用私有交接文件。未找到快照时不能凭代码声称恢复了调查。
5. `python -m unittest discover -s tests -v`；`python src/research.py export`。对照覆盖台账续查，不重复创建。
6. 飞书先 `python src/feishu_sync.py plan`。已有相同记录跳过，差异先审查。结果不明先完整回读，不重发创建请求。所有参与表完成分页并逐字段核验。
7. 更新数据、证据、缺口、状态与本地快照。保存代码版本和快照校验。调查达到全量边界之前，始终标记部分完成。
