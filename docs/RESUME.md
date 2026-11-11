# 接续

1. 阅读 PRD、AGENTS、STATUS、私有 exports/coverage_summary.json 和 receipts/validation.json。
2. 确认当前目录是独立项目。不要使用 ebook 配置、凭据或工作流。只有一个写入端。
3. 在新设备拉代码后，单独恢复匹配的数据快照；对 ZIP 内 manifest.json 逐文件校验 SHA256；恢复 SQLite 后跑 integrity_check 和 foreign_key_check。
4. 各设备独立登录 lark-cli，用户已指定飞书只用 CLI。真实 Base 配置不从Git推断；使用私有交接文件。未找到快照时不能凭代码声称恢复了调查。
5. `python -m unittest discover -s tests -v`；`python src/research.py export`。对照覆盖台账续查，不重复创建。
6. 飞书先 `python src/feishu_sync.py plan`，增量使用 `python src/feishu_incremental.py --run 唯一批次名`。逐表保存差异、dry-run、实际写入和完整分页回读；超过2000行继续翻页。已有相同记录跳过，远端人工改动与基线冲突时停止。结果不明先回读，不重发创建请求。所有关联逐项核验。
7. 更新数据、证据、缺口、状态与本地快照。保存代码版本和快照校验。调查达到全量边界之前，始终标记部分完成。
8. 已建晋江候选的公开详情可用 `python src/finish_candidate_details.py --start 下一批编号 --size 100` 接续。它是当前进程的有限批次，不是定时任务；访问受阻即停该来源，每批导出、验证、CLI同步回读、快照。查看 data/p1-*.json 的实际结果，不跳过尚未完成同步的批次。
9. 详情核验与商业媒介核查分开：详情采齐不表示商业调查完成。长佩DOM捕获先保存私有文件，其他写入进程退出后才导入；保持单写入端。
10. 存在 data/queued-batches.json 时逐项核对已入库和已回读状态。新增证据来源/精度字段由 `python src/feishu_evidence_fields.py` 幂等建列并回读；之后仍须运行增量同步填值、完整回读。不要将建列视为数据同步完成。
11. 作品页明确显示“被锁定或删除文章”时，保留该候选、原响应和缺口，不尝试绕过；该作品可从普通详情队列暂时隔离，继续其他作品。无法识别的空页、认证或拒绝仍暂停来源，不能仅凭解析失败断言整站不可访问。
12. 飞书写入成功但立即读回旧值时，程序有限次只读重查并留存每次结果，不重发写入；仍不一致则停止核对。书名含嵌套书名号时用官方作者链接定位边界，不能把书名尾部误作作者。
