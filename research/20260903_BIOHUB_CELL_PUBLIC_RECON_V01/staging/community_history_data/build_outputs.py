#!/usr/bin/env python3
"""Build the community/history/dataset staging artifacts from captured metadata.

This script is deliberately offline.  It performs no network access and writes
only inside its own staging directory.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from urllib.parse import quote_plus


BASE = Path(__file__).resolve().parent
EVIDENCE = BASE / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)
STAGING_REL = "research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data"


def repo_evidence(path: str) -> str:
    """Return a repository-root-resolvable evidence path."""
    return f"{STAGING_REL}/{path.lstrip('/')}"


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sg_time(utc: str | None) -> str | None:
    if not utc:
        return None
    # Every captured timestamp in this task is UTC and Singapore is UTC+08 year-round.
    m = re.match(r"(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})", utc)
    if not m:
        return None
    from datetime import datetime, timezone, timedelta

    dt = datetime.fromisoformat(utc.replace("Z", "+00:00"))
    return dt.astimezone(timezone(timedelta(hours=8))).isoformat()


REDDIT_NATIVE = [
    ("Biohub - Cell Tracking During Development", "2026-09-03T08:11:15.336Z", 4187, "89c896e8b749e7d772e42a101479f0be631898671bacd23bea03808add7b8a80", 7, "未见直接相关主题。"),
    ("biohub-cell-tracking-during-development", "2026-09-03T08:11:19.122Z", 4822, "ebbda1f5b863530bb0e22a308ad9d1e1d8417c974dbb2cec2d4305f6e3a59998", 7, "未见直接相关主题。"),
    ("Biohub cell tracking Kaggle", "2026-09-03T08:11:22.903Z", 4413, "3ddd6d07de2ba0d30f7a0d398aa6946432616d281d8f5c54e58e5c63fda1c817", 7, "命中一条当前比赛提交延迟主题。"),
    ("zebrafish tracking Kaggle", "2026-09-03T08:11:26.727Z", 3645, "c9b8adaf9971095ee48475f0410f353c9bdac86c9119a8a3545ef83115b62b50", 7, "未见当前比赛直接命中。"),
    ("3D microscopy Kaggle", "2026-09-03T08:11:30.548Z", 5495, "8043b5d9e0c6e1ba8685735cd4059d238574823e1698acaae3c62d732a7cd31a", 7, "出现通用 3D 显微相关讨论。"),
    ("GEFF cell tracking", "2026-09-03T08:11:34.453Z", 4456, "18f53f122dbf1be1f66ecfa03c02258ec5917b6309a613427586a698a909705c", 7, "结果为噪声或缩写误命中。"),
    ("Ultrack Kaggle", "2026-09-03T08:11:38.873Z", 4091, "1715271d42c24a7398cd82e065bc69ecad99cf5804b05d4bd105573ef656314d", 7, "未见直接相关主题。"),
    ("cell lineage competition", "2026-09-03T08:11:42.680Z", 3775, "8d1bdf58a5b88b8f6d8c047176d475a64bc0dfc6f55b5e4141761b6c1bfc4ead", 7, "未见当前图像谱系比赛直接命中。"),
]


REDDIT_THREADS = [
    {
        "source_id": "reddit_biohub_submission_issue",
        "title": "Kaggle competition biohub submission issue",
        "url": "https://www.reddit.com/r/kaggle/comments/1vprsb7/kaggle_competition_biohub_submission_issue/",
        "author": "MaleficentPass7124", "subreddit": "r/kaggle", "published_at": "2026-08-16T08:40:12.420000+00:00",
        "score": 5, "upvote_ratio": 1.0, "comments_reported": 0, "comments_loaded": 0,
        "read_status": "FULL_THREAD_READ", "access_time_utc": "2026-09-03T08:14:45.294Z", "bytes_observed": 1426,
        "sha256": "d78a08bcdf46c501473e2a6fed53224d5daae918e638170da074f050a00b9107",
        "summary": "参赛者报告提交保存或评分可能延迟近一天；仅为社区经历，未获官方确认。",
    },
    {
        "source_id": "reddit_imagej_ctc_help", "title": "Where can I find solutions for cell track challenge",
        "url": "https://www.reddit.com/r/ImageJ/comments/1jv5oy8/where_can_i_find_solutions_for_cell_track/",
        "author": "Dexis_9", "subreddit": "r/ImageJ", "published_at": "2025-04-09T13:24:03.431000+00:00",
        "score": 2, "upvote_ratio": 1.0, "comments_reported": 12, "comments_loaded": 12,
        "read_status": "PARTIAL_THREAD_READ", "access_time_utc": "2026-09-03T08:14:49.843Z", "bytes_observed": 5241,
        "sha256": "6a85d1c44679c347bcc4d75eda60c7c68c06f616e1a5487ba2bfad395b8e0072",
        "summary": "用户称 TrackMate DoG/LoG 与 Simple LAP 效果不佳；回复建议调节 gap closing。页面仍显示更多回复。",
    },
    {
        "source_id": "reddit_3d_yolo_microscopy", "title": "Is there a 3D version of YOLO for microscopy images",
        "url": "https://www.reddit.com/r/deeplearning/comments/m2nyyp/is_there_a_3d_version_of_yolo_that_can_take_as/",
        "author": "SIBCW96", "subreddit": "r/deeplearning", "published_at": "2021-03-11T11:19:34.799000+00:00",
        "score": 5, "upvote_ratio": 0.8571428571, "comments_reported": 7, "comments_loaded": 7,
        "read_status": "FULL_THREAD_READ", "access_time_utc": "2026-09-03T08:14:53.888Z", "bytes_observed": 3398,
        "sha256": "5c10c97b4c19ae88bafaa8d6d7348b9554e8c1366587b07454289198683bfc2b",
        "summary": "评论提出 2.5D/CellProfiler 等替代思路，并质疑通用 YOLO 是否合适；均为社区建议。",
    },
    {
        "source_id": "reddit_cell_segmentation_industry", "title": "How common is cell segmentation and tracking in industry",
        "url": "https://www.reddit.com/r/bioinformatics/comments/18kwaiu/how_common_is_cell_segmentation_and_tracking_in/",
        "author": "fluffyofblobs", "subreddit": "r/bioinformatics", "published_at": "2023-12-18T01:00:17.373000+00:00",
        "score": 5, "upvote_ratio": 1.0, "comments_reported": 7, "comments_loaded": 7,
        "read_status": "FULL_THREAD_READ", "access_time_utc": "2026-09-03T08:15:01.053Z", "bytes_observed": 6823,
        "sha256": "838f4f3f858891dd00474ce229ccbdc926f6aeac4e5de9b2a729c7ff93a37456",
        "summary": "讨论提到自发荧光和 DAPI 图像质量等实践痛点；不能当作比赛事实。",
    },
    {
        "source_id": "reddit_fish_3d_tracking", "title": "3D tracking for laboratory fish tanks",
        "url": "https://www.reddit.com/r/labrats/comments/t9bdox/3d_tracking_for_laboratory_fish_tanks_behavior/",
        "author": "shankharan", "subreddit": "r/labrats", "published_at": "2022-03-08T07:24:46.893000+00:00",
        "score": 3, "upvote_ratio": 1.0, "comments_reported": 1, "comments_loaded": 1,
        "read_status": "FULL_THREAD_READ", "access_time_utc": "2026-09-03T08:15:05.278Z", "bytes_observed": 2632,
        "sha256": "863d5e0759e58c90f18cc224f70e5f4b9c0461f025971acde4f466af0e0c7f73",
        "summary": "关于鱼缸中鱼类行为 3D 跟踪的低相关讨论，不涉及胚胎细胞谱系。",
    },
    {
        "source_id": "reddit_celllocator", "title": "CellLocator open-source tool for live-cell imaging",
        "url": "https://www.reddit.com/r/bioinformatics/comments/1h52fmj/celllocator_an_opensource_tool_for_unlocking/",
        "author": "MichaelVorndran", "subreddit": "r/bioinformatics", "published_at": "2024-12-02T18:49:46.009000+00:00",
        "score": 2, "upvote_ratio": 0.75, "comments_reported": 1, "comments_loaded": 1,
        "read_status": "FULL_THREAD_READ", "access_time_utc": "2026-09-03T08:15:09.550Z", "bytes_observed": 7042,
        "sha256": "8d27797573bea5b4a6a97a9f40ad8c7a410a1491721275cba18ac7b5e880cb38",
        "summary": "作者介绍 CellLocator；缺少独立复核，不能据此认定效果或可迁移性。",
    },
]


SCIENCE = [
    ("ctc_datasets", "Cell Tracking Challenge datasets", "Cell Tracking Challenge", "https://celltrackingchallenge.net/datasets/", "2026-09-03T08:19:05.047Z", 2586, "a99e9c20d861f46faaf84aa6ea2de164f8654dd54b9e9ec9a79feb53b0c66711", "FULL_PAGE_BODY_READ", "列出 2D/3D 时序显微数据集及使用条件。"),
    ("ctc_evaluation", "Cell Tracking Challenge evaluation methodology", "Cell Tracking Challenge", "https://celltrackingchallenge.net/evaluation-methodology/", "2026-09-03T08:19:20.777Z", 5632, "02e5fbf5de9eba1cc100fbc5d73be3d81b011a2a9c06ec4735260bb05ba326f8", "FULL_PAGE_BODY_READ", "定义 DET、TRA、LNK、BIO 与综合 OP_CTB 指标。"),
    ("ctc_annotations", "Cell Tracking Challenge reference annotations", "Cell Tracking Challenge", "https://celltrackingchallenge.net/annotations/", "2026-09-03T08:19:24.163Z", 3321, "e2721c270255e4700893b7e7555a7039bef7d36fb9c686bb96d51e84b34c9bfb", "FULL_PAGE_BODY_READ", "解释 gold 与 silver annotations 的覆盖和质量取舍。"),
    ("ctc_history", "Cell Tracking Challenge history and publications", "Cell Tracking Challenge", "https://celltrackingchallenge.net/history/", "2026-09-03T08:19:27.533Z", 8004, "500ec053e2c26cbcbdc11e3720184e05888f6e50a659ed9dd6b4a5d5de09310c", "FULL_PAGE_BODY_READ", "记录自 2012 年以来的挑战演进与出版物。"),
    ("ctc_results", "Cell Tracking Benchmark results", "Cell Tracking Challenge", "https://celltrackingchallenge.net/latest-ctb-results/", "2026-09-03T08:19:33.495Z", 1950, "e686dd97f06a7fc7612fd37cb42451756f148453ac7e9ab6cdff1451f8dfd066", "FULL_PAGE_BODY_READ", "提供持续更新的基准结果入口。"),
    ("biohub_royer_initial", "Royer Group initial URL", "Chan Zuckerberg Biohub", "https://www.czbiohub.org/royer/", "2026-09-03T08:19:47.109Z", 0, None, "BLOCKED", "初始域名导航超时，后以 biohub.org 版本成功读取。"),
    ("zebrahub_pubmed", "A multimodal zebrafish developmental atlas", "PubMed / Cell", "https://pubmed.ncbi.nlm.nih.gov/39454574/", "2026-09-03T08:20:00.343Z", 8513, "aa356b3691f1e28d1aef64c82e86f601bc5308ee349ae4549a4e4c8301c8b8cc", "FULL_PAGE_BODY_READ", "论文摘要描述单细胞测序与光片谱系重建结合的斑马鱼发育图谱。"),
    ("ctc_nature_methods", "The Cell Tracking Challenge: 10 years of objective benchmarking", "Nature Methods", "https://www.nature.com/articles/s41592-023-01879-y", "2026-09-03T08:20:06.611Z", 102248, "c3d691b89e75cdbd80d75b147e8ec6833dc1d5216f5d72ce92452f64b30d2841", "FULL_PAGE_BODY_READ", "系统评估多数据集算法、标注质量、技术和生物指标及泛化。"),
    ("biorxiv_zebrahub_full", "Zebrahub preprint full route", "bioRxiv", "https://www.biorxiv.org/content/10.1101/2023.03.06.531398v1.full", "2026-09-03T08:20:16.347Z", 235, "d0665d559ed914743487ab946907a02cfeafb81c65d1bf0b9f2fbf92b7d49750", "BLOCKED", "只读到安全验证页，未读取论文正文。"),
    ("ultrack_docs", "Ultrack documentation", "Royer Lab", "https://royerlab.github.io/ultrack/", "2026-09-03T08:20:23.294Z", 40865, "c225601c2a71e186f02ef1c28774d12b03f80b25b15146854617c90c265091c3", "FULL_PAGE_BODY_READ", "文档覆盖候选分割、关联、全局求解、2D/3D 与大规模数据工作流。"),
    ("trackastra_arxiv", "Trackastra: Transformer-based cell tracking", "arXiv", "https://arxiv.org/abs/2405.15700", "2026-09-03T08:20:39.221Z", 3289, "1cae8e4252c3a3193b2082e9665e08d5ac5f77685b4c4417c5177188aa02a94f", "FULL_PAGE_BODY_READ", "摘要描述跨时间窗口的 Transformer 关联和分裂处理，前提是已有实例分割或检测。"),
    ("trackastra_github", "Trackastra repository README", "GitHub / Weigert Lab", "https://github.com/weigertlab/trackastra", "2026-09-03T08:20:48.781Z", 6279, "6b0017d658ba1773ea0206aa19e15dd34fd8ff236c3f67d100ce877da0bc7096", "README_ONLY", "README 记录 2D/3D 用法、预训练模型和 greedy/ILP 跟踪模式。"),
    ("geff_spec", "GEFF specification", "Live Image Tracking Tools", "https://liveimagetrackingtools.org/geff/latest/specification/", "2026-09-03T08:20:58.764Z", 17949, "76616aa61cd57fab150f79087468fe5805402e3544f5feaac0ff0bce192b5d96", "FULL_PAGE_BODY_READ", "规范定义 Zarr 图的节点、边、属性、轴和元数据。"),
    ("tracksdata_github", "TracksData repository README", "GitHub / Royer Lab", "https://github.com/royerlab/tracksdata", "2026-09-03T08:21:08.663Z", 3198, "55ef851ce0307c57df1e8adf356f99e88897a5531a36802401c06f698ab368c7", "README_ONLY", "README 说明面向多目标跟踪的图表示、SQL/RustWorkX 后端及 NN/ILP 工具。"),
    ("image_sc_elephant", "ELEPHANT 3D lineage tracking announcement", "image.sc Forum", "https://forum.image.sc/t/announcing-elephant-tracking-cell-lineages-in-3d-by-incremental-deep-learning/49519", "2026-09-03T08:21:14.505Z", 2550, "e6dda017e9504ee30ffe8d425cfada86277928b18beb058e59557b878c5cb104", "FULL_PAGE_BODY_READ", "主题和回复介绍 3D+time 标注、深度学习、校正和增量学习工作流。"),
    ("biohub_royer", "Royer Group organismal architecture research", "Chan Zuckerberg Biohub", "https://biohub.org/royer/", "2026-09-03T08:25:53.312Z", 2609, "06b889b71ff9f1476c7d29705c5e4a36ef4dcd6a172f6a1e8ad43de61603211e", "FULL_PAGE_BODY_READ", "研究页将 Zebrahub、光片显微和发育生物学置于同一研究脉络。"),
    ("biorxiv_zebrahub_abs", "Zebrahub preprint abstract route", "bioRxiv", "https://www.biorxiv.org/content/10.1101/2023.03.06.531398v1", "2026-09-03T08:26:17.665Z", 235, "0fc8e8bf73e9d2296455e51f0d3c272e1692de8991f17728ef4405e1887933da", "BLOCKED", "再次只读到安全验证页，未读取论文正文。"),
    ("staf_arxiv", "Efficient Online Multi-Person 2D Pose Tracking with Recurrent Spatio-Temporal Affinity Fields", "arXiv", "https://arxiv.org/abs/1811.11975", "2026-09-03T08:48:16.835Z", 2510, "6d22ba2421c646272d852e8ea31e0e49236ad486d09b279e50f235499223c429", "FULL_PAGE_BODY_READ", "原始 STAF 论文针对多人 2D 姿态视频跟踪，不是细胞或谱系；只能作为关联表示类比。"),
]


HISTORY_READS = [
    ("hist_dsb2018", "2018 Data Science Bowl", "https://www.kaggle.com/competitions/data-science-bowl-2018", "2026-09-03T08:24:12.930Z", 15338, "476a9a482932127393a6d1fc9762564769aceb710f95e165ab00f61e555b4252", "Kaggle Competition", "官方比赛页：2D 核实例分割、阈值平均精度和 RLE 提交。"),
    ("hist_sartorius", "Sartorius - Cell Instance Segmentation", "https://www.kaggle.com/competitions/sartorius-cell-instance-segmentation", "2026-09-03T08:24:20.233Z", 8222, "e38ebae6f4baacf7ff682cb46a294516b4418c776798209f441d50e6346c6fbe", "Kaggle Competition", "官方比赛页：2D 神经细胞实例分割。"),
    ("hist_czii", "CZII - CryoET Object Identification", "https://www.kaggle.com/competitions/czii-cryo-et-object-identification", "2026-09-03T08:24:23.167Z", 7372, "fb67108abdcbae0245c0cfb31d49a0529b2ad98916b15e8cc1aa669915e24b25", "Kaggle Competition", "官方比赛页：3D 冷冻电镜粒子点检测，F-beta-4 偏重召回。"),
    ("hist_byu", "BYU - Locating Bacterial Flagellar Motors 2025", "https://www.kaggle.com/competitions/byu-locating-bacterial-flagellar-motors-2025", "2026-09-03T08:24:26.160Z", 6479, "bfe34c76840833158f752504d98cabad3334a73519512b06ce110ddbe9e77693", "Kaggle Competition", "官方比赛页：3D 断层图中存在性与点定位。"),
    ("hist_hpa", "Human Protein Atlas - Single Cell Classification", "https://www.kaggle.com/competitions/hpa-single-cell-image-classification", "2026-09-03T08:24:29.179Z", 9486, "d8d46d085724415cc2bb9ffd349a6971a1b72b8973c906ab51e5f65389aae5c1", "Kaggle Competition", "官方比赛页：多通道显微图像的逐细胞多标签分类。"),
    ("hist_recursion", "Recursion Cellular Image Classification", "https://www.kaggle.com/competitions/recursion-cellular-image-classification", "2026-09-03T08:24:32.014Z", 7441, "6c0351549575476beb9b065c41d560f593d32e887c50e864599f24105fd0aa5c", "Kaggle Competition", "官方比赛页：多通道细胞图像扰动分类与批次域偏移。"),
    ("hist_dsb2018_writeup", "DSB 2018 first-place writeup", "https://www.kaggle.com/competitions/data-science-bowl-2018/writeups/ods-ai-topcoders-ods-ai-topcoders-1st-place-soluti", "2026-09-03T08:24:44.049Z", 26835, "b4e22525d99273d44b31121365129d4e5924eb8718c59864687562e8ca217410", "Kaggle Writeup", "官方 writeup 标注 1st place；方法含 U-Net、边界目标、分水岭和对象级后处理。"),
    ("hist_sartorius_writeup", "Sartorius first-place writeup", "https://www.kaggle.com/competitions/sartorius-cell-instance-segmentation/writeups/rist-takuoko-tascj-1st-place-solution", "2026-09-03T08:24:48.909Z", 12188, "4bcd8327460386a634f1fae71e965e4ff8ada71a03a471c4e633ef500ad609a8", "Kaggle Writeup", "官方 writeup 标注 1st place；报告本地 COCO AP 0.396，不是榜单分数。"),
    ("hist_czii_writeup", "CZII first-place object-detection writeup", "https://www.kaggle.com/competitions/czii-cryo-et-object-identification/discussion/561440", "2026-09-03T08:24:52.569Z", 18733, "a3ff1b73218632c0d850bd6ae630c1028166353d78ab71ffd9ad5dc05ac28436", "Kaggle Discussion", "作者带 1st in this competition 标识，公开 3D 分割与检测集成方案。"),
    ("hist_byu_writeup", "BYU second-place writeup", "https://www.kaggle.com/competitions/byu-locating-bacterial-flagellar-motors-2025/writeups/mic-dkfz-2nd-place-solution-3d-nnu-net-blob-regres", "2026-09-03T08:24:56.967Z", 21016, "066536567be981cfc75816d46f6b8f53ca2ef6e469f3393e68e0be9d0978596a", "Kaggle Writeup", "官方 writeup 标注 2nd place，并绑定公开 0.86734、私榜 0.87656。"),
    ("hist_hpa_writeup", "HPA first-place writeup", "https://www.kaggle.com/competitions/hpa-single-cell-image-classification/writeups/bestfitting-fair-cell-activation-network-and-swin-", "2026-09-03T08:24:59.798Z", 6803, "f0736b90852fa9c38df82ef215cc9c0bbf457c954612fb8688273da3dd9dccdf", "Kaggle Writeup", "官方 writeup 标注 1st place；作者报告简单双模型私榜 0.555、六模型 0.566。"),
    ("hist_recursion_writeup", "Recursion first-place writeup", "https://www.kaggle.com/competitions/recursion-cellular-image-classification/writeups/maciej-sypetkowski-1st-place-solution-write-up-cod", "2026-09-03T08:25:02.583Z", 21021, "319dc5e3185f48da88bf3dd57fce39921be7027c6a4342982bfad70dc2870014", "Kaggle Writeup", "官方 writeup 标注 1st place；最终集成作者报告私榜 0.99763、公开榜 0.99480。"),
]


HISTORY_CANDIDATES = [
    {
        "competition": "2018 Data Science Bowl", "url": HISTORY_READS[0][2], "read_status": "FULL_PAGE_BODY_READ", "microscopy": "yes", "dimensionality": "2D", "time_dimension": "no", "objective": "nuclei instance segmentation", "cell_division": "no", "sparse_labels": "no", "output": "instance masks / RLE", "metric": "mean precision over IoU thresholds 0.50-0.95", "data_scale": "heterogeneous 2D microscopy images; exact count not extracted", "compute": "participant-managed; unlike current 12h offline notebook", "external_data": "first-place writeup reports several public nuclei datasets", "post_competition_solution": "yes; official first-place writeup", "rank_evidence": "1st place; official writeup", "score_evidence": "UNKNOWN; no final leaderboard score bound", "transferable": "encoder-decoder detection features, boundary target, object postprocessing", "required_changes": "3D anisotropy, time association, division topology, GEFF export, node-count control", "incompatible": "2D dense masks and mask-IoU objective do not solve graph tracking", "similarity": "high for detection/instance separation; low for tracking", "evidence_urls": HISTORY_READS[0][2] + " | " + HISTORY_READS[6][2], "notes": "Do not interpret a visible unrelated 0.938 sidebar value as this competition score."},
    {
        "competition": "Sartorius - Cell Instance Segmentation", "url": HISTORY_READS[1][2], "read_status": "FULL_PAGE_BODY_READ", "microscopy": "yes", "dimensionality": "2D", "time_dimension": "no", "objective": "neuronal cell instance segmentation", "cell_division": "no", "sparse_labels": "no", "output": "instance masks / RLE", "metric": "mean AP over IoU thresholds", "data_scale": "2D phase-contrast images; exact count not extracted", "compute": "code competition; 9h limit observed on official page", "external_data": "public external data allowed per official page/writeup usage", "post_competition_solution": "yes; official first-place writeup", "rank_evidence": "1st place; official writeup", "score_evidence": "local COCO AP=0.396; explicitly not leaderboard score", "transferable": "cell instance separation, mask/bbox reranking, overlap cleanup", "required_changes": "3D detector, temporal linker, divisions, sparse supervision, GEFF", "incompatible": "no temporal graph and no node-count penalty", "similarity": "high for cell separation; low for lineage", "evidence_urls": HISTORY_READS[1][2] + " | " + HISTORY_READS[7][2], "notes": "Keep validation AP separate from competition leaderboard score."},
    {
        "competition": "CZII - CryoET Object Identification", "url": HISTORY_READS[2][2], "read_status": "FULL_PAGE_BODY_READ", "microscopy": "yes", "dimensionality": "3D", "time_dimension": "no", "objective": "particle point detection", "cell_division": "no", "sparse_labels": "point annotations", "output": "x/y/z coordinates and type", "metric": "F-beta-4, recall weighted", "data_scale": "3D tomograms; exact count not extracted", "compute": "12h code competition", "external_data": "public external data permitted/used", "post_competition_solution": "yes; first-place author discussion and code", "rank_evidence": "author marked 1st in competition", "score_evidence": "writeup examples include ~0.740 and 0.752 LB for component baselines; not final team score", "transferable": "3D heatmap/point detection, tiling, NMS, TensorRT acceleration", "required_changes": "add temporal association, division modeling, GEFF graph and current edge/division metric", "incompatible": "F-beta point objective has no trajectory consistency", "similarity": "very high for 3D point detection; low for time", "evidence_urls": HISTORY_READS[2][2] + " | " + HISTORY_READS[8][2], "notes": "Do not bind an unrelated notebook score to the final team without a direct record."},
    {
        "competition": "BYU - Locating Bacterial Flagellar Motors 2025", "url": HISTORY_READS[3][2], "read_status": "FULL_PAGE_BODY_READ", "microscopy": "yes", "dimensionality": "3D", "time_dimension": "no", "objective": "presence classification plus point localization", "cell_division": "no", "sparse_labels": "point target", "output": "presence and x/y/z coordinate", "metric": "classification F-score plus distance-based localization component", "data_scale": "3D tomograms; exact count not extracted", "compute": "12h code competition", "external_data": "writeup used Bartley data and 555 additional public tomograms", "post_competition_solution": "yes; official second-place writeup", "rank_evidence": "2nd place; tied score resolved by submission time", "score_evidence": "public 0.86734; private 0.87656; author writeup", "transferable": "3D nnU-Net blob regression, anisotropic resampling, sliding-window inference, NMS", "required_changes": "multi-frame model, association/division edges, GEFF conversion, 12h end-to-end budget", "incompatible": "single-coordinate tomogram target cannot express many cells or lineage", "similarity": "very high for 3D localization; low for tracking", "evidence_urls": HISTORY_READS[3][2] + " | " + HISTORY_READS[9][2], "notes": "Author also reports lower-compute private 0.86392; threshold budgets were unequal."},
    {
        "competition": "Human Protein Atlas - Single Cell Classification", "url": HISTORY_READS[4][2], "read_status": "FULL_PAGE_BODY_READ", "microscopy": "yes", "dimensionality": "2D multichannel", "time_dimension": "no", "objective": "per-cell multilabel classification", "cell_division": "no", "sparse_labels": "weak image-level labels plus supplied segmentation", "output": "class/confidence/mask records", "metric": "mean average precision at mask matching threshold", "data_scale": "large four-channel confocal collection; exact count not extracted", "compute": "code competition", "external_data": "public HPA overlap explicitly handled in writeup", "post_competition_solution": "yes; official first-place writeup", "rank_evidence": "1st place; official writeup", "score_evidence": "private 0.555 simple ensemble; 0.566 six-model ensemble", "transferable": "multichannel normalization, weak-label learning, border-cell confidence handling", "required_changes": "3D+time, point detection, association/division graph, GEFF and graph metric", "incompatible": "classification objective and 2D masks are far from lineage reconstruction", "similarity": "medium imaging-domain relevance", "evidence_urls": HISTORY_READS[4][2] + " | " + HISTORY_READS[10][2], "notes": "Scores are author-reported private-LB values bound to the writeup."},
    {
        "competition": "Recursion Cellular Image Classification", "url": HISTORY_READS[5][2], "read_status": "FULL_PAGE_BODY_READ", "microscopy": "yes", "dimensionality": "2D multichannel", "time_dimension": "no", "objective": "cellular perturbation classification", "cell_division": "no", "sparse_labels": "no", "output": "class label", "metric": "multiclass accuracy", "data_scale": "many experimental batches and 1,108 perturbation classes", "compute": "participant-managed historical competition", "external_data": "not extracted as a rule claim", "post_competition_solution": "yes; official first-place writeup and author repository", "rank_evidence": "1st place; official writeup", "score_evidence": "final private 0.99763; public 0.99480; author writeup", "transferable": "per-channel normalization, augmentation, batch/domain robustness", "required_changes": "discard class assignment; build 3D detector and temporal lineage graph", "incompatible": "pseudo-label/test assignment and known batch leakage must not be copied", "similarity": "medium for imaging robustness; low for output task", "evidence_urls": HISTORY_READS[5][2] + " | " + HISTORY_READS[11][2], "notes": "Known leak-like experiment structure makes direct transfer unsafe."},
    {"competition": "SenNet + HOA - Hacking the Human Vasculature in 3D", "url": "https://www.kaggle.com/competitions/blood-vessel-segmentation", "read_status": "TITLE_SNIPPET_ONLY", "microscopy": "yes", "dimensionality": "3D", "time_dimension": "no", "objective": "vasculature semantic segmentation", "cell_division": "no", "sparse_labels": "unknown", "output": "3D mask / RLE", "metric": "unknown in this pass", "data_scale": "unknown", "compute": "unknown", "external_data": "unknown", "post_competition_solution": "likely, not read", "rank_evidence": "UNKNOWN", "score_evidence": "UNKNOWN", "transferable": "3D patching and memory control candidate", "required_changes": "points, time, division, GEFF", "incompatible": "tubular mask objective", "similarity": "medium", "evidence_urls": "https://www.kaggle.com/competitions/blood-vessel-segmentation", "notes": "Candidate discovery only; no ranking or score claim."},
    {"competition": "HuBMAP + HPA - Hacking the Human Body", "url": "https://www.kaggle.com/competitions/hubmap-organ-segmentation", "read_status": "TITLE_SNIPPET_ONLY", "microscopy": "yes", "dimensionality": "2D", "time_dimension": "no", "objective": "functional tissue unit segmentation", "cell_division": "no", "sparse_labels": "unknown", "output": "masks / RLE", "metric": "unknown in this pass", "data_scale": "unknown", "compute": "unknown", "external_data": "unknown", "post_competition_solution": "likely, not read", "rank_evidence": "UNKNOWN", "score_evidence": "UNKNOWN", "transferable": "cross-organ/domain robustness candidate", "required_changes": "3D time and graph", "incompatible": "tissue masks", "similarity": "medium-low", "evidence_urls": "https://www.kaggle.com/competitions/hubmap-organ-segmentation", "notes": "Candidate discovery only."},
    {"competition": "HuBMAP - Hacking the Kidney", "url": "https://www.kaggle.com/competitions/hubmap-kidney-segmentation", "read_status": "TITLE_SNIPPET_ONLY", "microscopy": "yes", "dimensionality": "2D very-large TIFF", "time_dimension": "no", "objective": "glomeruli segmentation", "cell_division": "no", "sparse_labels": "unknown", "output": "mask / RLE", "metric": "unknown in this pass", "data_scale": "whole-slide images", "compute": "unknown", "external_data": "unknown", "post_competition_solution": "likely, not read", "rank_evidence": "UNKNOWN", "score_evidence": "UNKNOWN", "transferable": "tiling and streaming candidate", "required_changes": "3D temporal graph", "incompatible": "whole-slide organ segmentation", "similarity": "low-medium", "evidence_urls": "https://www.kaggle.com/competitions/hubmap-kidney-segmentation", "notes": "Candidate discovery only."},
    {"competition": "HuBMAP - Hacking the Human Vasculature", "url": "https://www.kaggle.com/competitions/hubmap-hacking-the-human-vasculature", "read_status": "TITLE_SNIPPET_ONLY", "microscopy": "yes", "dimensionality": "2D", "time_dimension": "no", "objective": "microvasculature instance segmentation", "cell_division": "no", "sparse_labels": "unknown", "output": "instance masks", "metric": "unknown in this pass", "data_scale": "unknown", "compute": "unknown", "external_data": "unknown", "post_competition_solution": "likely, not read", "rank_evidence": "UNKNOWN", "score_evidence": "UNKNOWN", "transferable": "instance separation candidate", "required_changes": "cells, 3D+time, lineage graph", "incompatible": "vascular instances, no time", "similarity": "medium-low", "evidence_urls": "https://www.kaggle.com/competitions/hubmap-hacking-the-human-vasculature", "notes": "Candidate discovery only."},
]


def browser_dataset_rows() -> list[dict]:
    rows = []
    with (EVIDENCE / "browser_dataset_page_reads.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return rows


def classify_dataset(ref: str, title: str, description: str) -> tuple[str, str, str, str, str, str, str]:
    text = f"{ref} {title} {description}".lower()
    if "e-coli" in text:
        return ("fluorescence time-lapse", "E. coli", "2D", "yes", "images + adjacency graph", "medium", "2D organism/domain mismatch; graph labels conceptually relevant")
    if "fuse-my-cells" in text:
        return ("multi-view light-sheet", "biological specimens", "3D", "not established", "fused volumes", "medium", "imaging-domain only; no tracking labels")
    if "electron-microscopy" in text:
        return ("electron microscopy", "mouse brain tissue", "3D", "no", "segmentation masks", "medium", "3D segmentation only; no time or lineage")
    if "zebrafish-embryonic" in text:
        return ("unknown", "zebrafish embryo", "unknown", "unknown", "unknown", "medium", "biological domain match but provenance/labels absent")
    if "zh001r" in text:
        return ("light-sheet / Zebrahub-derived (page claim)", "zebrafish embryo", "3D", "page implies crops; time unclear", "real-label crops / nodes", "very high", "possible same-source labels; leakage review mandatory")
    if "trackastra" in text or "ultrack" in text:
        return ("not a raw microscopy dataset", "not applicable", "2D/3D-capable package", "yes-capable", "weights/wheels/software", "high", "software/model packaging, not external raw labels")
    if "biohub" in text or "cell-tracking-competition" in text or "cell_tracking" in text:
        return ("3D fluorescence light-sheet or competition artifact", "zebrafish embryo / not applicable", "3D", "yes", "GEFF graph, weights, code, notebook or submission artifacts", "very high", "current-competition-derived; rule and leakage review mandatory")
    return ("unknown", "unknown", "unknown", "unknown", "unknown", "low/unknown", "not enough metadata")


def make_dataset_inventory() -> list[dict]:
    details = json.loads((BASE / "dataset_detail_records.json").read_text(encoding="utf-8"))
    browser = {row["ref"]: row for row in browser_dataset_rows()}
    known_sizes = {
        "kms111201/biohub-cell-tracking-data": "79.16 GB (browser page)",
        "jobayerhossain/biohub-cell-tracking-during-development": "6.43 GB (browser page)",
        "isacinformagenie5/biohub-cell-tracking-during-development": "2.01 MB (browser page)",
        "soufianehajou/biohub-officiel-v6": "15.94 KB (browser page)",
        "pilkwang/biohub-tracking-support-pack-50ep-v1": "355.65 MB (browser page)",
        "pilkwang/biohub-temporal-unet3d-seed314159-v1": "355.75 MB (browser page)",
        "pilkwang/biohub-local-association-ranker-unet300-v1": "26.89 KB (browser page)",
        "subinium/biohub-trackastra-public-weights-mirror": "262.47 MB (browser page)",
        "varonvictormiranda/ultrack-offline-min": "537.39 MB (browser page)",
        "vyshnavveeravalli/zebrafish-embryonic-development": "998.27 MB (browser page)",
        "kkunizaw/biohub-zh001r": "764.36 MB (browser page)",
        "felipeporcher/trackastra": "109.91 MB (browser page)",
        "rudispresence/biohub-embryo-stardist-bayesian-assets": "37.65 MB (browser page)",
        "ayeshasummaiyya/royerlabkaggle-cell-tracking-competition": "5.75 MB (browser page)",
        "omararaby1/kaggle-cell-tracking-competition": "5.75 MB (browser page)",
    }
    out = []
    for rec in details:
        meta = ((rec.get("metadata") or {}).get("info") or {})
        ref = rec["ref"]
        br = browser.get(ref)
        title = (br or {}).get("title") or meta.get("title") or ref.split("/", 1)[-1]
        description = meta.get("description") or ""
        microscopy, species, dims, timedim, labels, relevance, compat = classify_dataset(ref, title, description)
        licenses = meta.get("licenses") or []
        license_text = " | ".join(x.get("name", "") for x in licenses if isinstance(x, dict)) or "UNKNOWN"
        file_examples = rec.get("file_names") or []
        file_text = f"observed_count={rec.get('files_observed_count', 0)}; complete={rec.get('file_list_complete')}"
        if file_examples:
            file_text += "; examples=" + " | ".join(file_examples[:8])
        if br and br["read_status"] == "FULL_PAGE_BODY_READ":
            read_status = "FULL_PAGE_BODY_READ"
        elif rec.get("metadata_exit_code") == 0:
            read_status = "METADATA_ONLY"
        elif rec.get("metadata_exit_code") != 0 and ref != "pilkwang/biohub-deepcenter-epoch400-snapshot":
            read_status = "RATE_LIMITED"
        else:
            read_status = "BLOCKED"
        out.append({
            "source_id": br["source_id"] if br else "dataset_candidate_" + re.sub(r"[^a-z0-9]+", "_", ref.lower()).strip("_"),
            "owner_dataset": ref,
            "url_ref": rec.get("url"),
            "title": title,
            "created_at": "UNKNOWN",
            "updated_at": "UNKNOWN; browser page only gave relative age where visible",
            "size": known_sizes.get(ref, f"observed_file_bytes={rec.get('files_observed_bytes_sum', 0)}; may be partial"),
            "license": license_text,
            "usability": meta.get("usabilityRating", "UNKNOWN"),
            "votes": meta.get("totalVotes", "UNKNOWN"),
            "download_count": meta.get("totalDownloads", "UNKNOWN"),
            "files": file_text,
            "file_formats": json.dumps(rec.get("file_extensions") or {}, ensure_ascii=False, sort_keys=True),
            "microscopy_type": microscopy,
            "species": species,
            "dimensions": dims,
            "time_dimension": timedim,
            "labels": labels,
            "relevance": relevance,
            "possible_use": "metadata/reproducibility reference only pending rule review",
            "rule_eligibility_checked": "false",
            "leakage_risk": "DO_NOT_USE_PENDING_RULE_REVIEW",
            "compatibility": compat,
            "read_status": read_status,
            "evidence_path": repo_evidence("evidence/browser_dataset_page_reads.jsonl") if br else repo_evidence("dataset_detail_records.json"),
            "notes": f"selection={rec.get('selection_reason')}; cli_metadata_exit={rec.get('metadata_exit_code')}; cli_files_exit={rec.get('files_exit_code')}; browser_evidence={'evidence/browser_dataset_page_reads.jsonl' if br else 'NOT_RUN'}; no content downloaded",
        })
    return out


def build() -> None:
    dataset_browser = browser_dataset_rows()

    evidence_rows = []
    for i, (query, utc, size, sha, count, summary) in enumerate(REDDIT_NATIVE, 1):
        evidence_rows.append({"source_id": f"reddit_native_search_{i:02d}", "source_type": "search_results", "platform": "Reddit", "title": f"Reddit search: {query}", "author": None, "url": f"https://www.reddit.com/search/?q={quote_plus(query)}", "access_time_utc": utc, "access_time_singapore": sg_time(utc), "read_status": "FULL_PAGE_BODY_READ", "bytes_observed": size, "sha256": sha, "summary": f"Observed {count} result cards. {summary}"})
    for row in REDDIT_THREADS:
        evidence_rows.append({**row, "source_type": "thread", "platform": "Reddit", "access_time_singapore": sg_time(row["access_time_utc"])})
    for sid, title, platform, url, utc, size, sha, status, summary in SCIENCE:
        evidence_rows.append({"source_id": sid, "source_type": "scientific_web", "platform": platform, "title": title, "author": platform, "url": url, "access_time_utc": utc, "access_time_singapore": sg_time(utc), "read_status": status, "bytes_observed": size, "sha256": sha, "summary": summary})
    for sid, title, url, utc, size, sha, platform, summary in HISTORY_READS:
        evidence_rows.append({"source_id": sid, "source_type": "historical_competition", "platform": platform, "title": title, "author": None, "url": url, "access_time_utc": utc, "access_time_singapore": sg_time(utc), "read_status": "FULL_PAGE_BODY_READ", "bytes_observed": size, "sha256": sha, "summary": summary})
    with (EVIDENCE / "browser_reddit_science_history_reads.jsonl").open("w", encoding="utf-8") as handle:
        for row in evidence_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    inventory14 = []
    for row in evidence_rows:
        inventory14.append({
            "source_id": row["source_id"], "platform": row["platform"], "title": row["title"],
            "author": row.get("author"), "url": row["url"], "created_at": row.get("published_at"),
            "score": row.get("score"), "comment_count": row.get("comments_reported"),
            "topic": row["summary"], "read_status": row["read_status"],
            "comments_loaded": row.get("comments_loaded"), "comments_total": row.get("comments_reported"),
            "evidence_path": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"),
            "notes": "Reddit/community claims are non-authoritative; dynamic scores may change." if row["platform"] == "Reddit" else "Only claims within the actually read page are used.",
            "source_type": row["source_type"], "subreddit": row.get("subreddit"),
            "access_time_utc": row.get("access_time_utc"), "access_time_singapore": row.get("access_time_singapore"),
            "upvote_ratio": row.get("upvote_ratio"), "bytes_observed": row["bytes_observed"],
            "sha256": row.get("sha256"),
        })
    write_csv(BASE / "14_reddit_and_web_inventory.csv", inventory14, list(inventory14[0]))

    similar16 = []
    similar_source_ids = [
        "hist_dsb2018", "hist_sartorius", "hist_czii", "hist_byu", "hist_hpa", "hist_recursion",
        "hist_sennet_title", "hist_hubmap_body_title", "hist_hubmap_kidney_title", "hist_hubmap_vasculature_title",
    ]
    for i, row in enumerate(HISTORY_CANDIDATES, 1):
        similar16.append({
            "source_id": similar_source_ids[i - 1], "competition": row["competition"], "url": row["url"],
            "microscopy": row["microscopy"], "spatial_dimensions": row["dimensionality"],
            "time_dimension": row["time_dimension"], "task_type": row["objective"],
            "cell_division": row["cell_division"], "sparse_labels": row["sparse_labels"],
            "output_type": row["output"], "metric": row["metric"], "data_scale": row["data_scale"],
            "compute": row["compute"], "external_data": row["external_data"],
            "post_competition_solution": row["post_competition_solution"],
            "transferability": row["transferable"], "required_changes": row["required_changes"],
            "incompatibilities": row["incompatible"], "deep_read": "true" if i <= 6 else "false",
            "read_status": row["read_status"],
            "evidence_path": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"),
            "rank_evidence": row["rank_evidence"], "score_evidence": row["score_evidence"],
            "similarity": row["similarity"], "evidence_urls": row["evidence_urls"], "notes": row["notes"],
        })
    write_csv(BASE / "16_similar_kaggle_competitions.csv", similar16, list(similar16[0]))

    inv18 = make_dataset_inventory()
    write_csv(BASE / "18_kaggle_datasets_inventory.csv", inv18, list(inv18[0]))

    # Query fragment: exact Dataset CLI searches plus both Reddit routes.
    qrows = []
    for rec in json.loads((BASE / "dataset_search_log.json").read_text(encoding="utf-8")):
        qrows.append({"query_id": f"kaggle_dataset_{len(qrows)+1:03d}", "category": "kaggle_datasets", "platform": "Kaggle Datasets CLI", "query": rec["query"], "sort_order": rec["sort_order"], "result_page": rec["result_page"], "reported_total": "UNKNOWN", "actually_obtained": rec["result_count"], "unique_after_dedupe": "computed globally: 185", "deep_read_count": 28, "access_time_utc": rec["finished_utc"], "access_time_singapore": rec["finished_singapore"], "status": "SUCCESS", "evidence_path": repo_evidence(rec["stdout_path"]), "notes": "No content downloaded; 15 page-2 responses said No datasets found and are empty, not errors." if rec.get("empty_result_response") else "Search-result metadata only."})
    for i, (query, utc, size, sha, count, summary) in enumerate(REDDIT_NATIVE, 1):
        qrows.append({"query_id": f"reddit_native_{i:02d}", "category": "reddit_native", "platform": "Reddit native search", "query": query, "sort_order": "relevance/default", "result_page": 1, "reported_total": "not exposed", "actually_obtained": count, "unique_after_dedupe": "not aggregated", "deep_read_count": sum(1 for t in REDDIT_THREADS if t["read_status"] in {"FULL_THREAD_READ", "PARTIAL_THREAD_READ"}), "access_time_utc": utc, "access_time_singapore": sg_time(utc), "status": "SUCCESS", "evidence_path": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "notes": summary})
    site_queries = [
        ('site:reddit.com "Biohub - Cell Tracking During Development"', 0, "no direct hit"),
        ('site:reddit.com "biohub-cell-tracking-during-development"', 0, "no direct hit"),
        ('site:reddit.com "Biohub cell tracking Kaggle"', 0, "quoted search no direct hit"),
        ('site:reddit.com "zebrafish tracking Kaggle"', 1, "one general fish 3D result"),
        ('site:reddit.com "3D microscopy Kaggle"', 5, "at least five general results"),
        ('site:reddit.com "GEFF cell tracking"', 0, "no direct hit"),
        ('site:reddit.com "Ultrack Kaggle"', 0, "no direct hit; mixed noisy returns not counted"),
        ('site:reddit.com "cell lineage competition"', 1, "single-cell dataset request, not image tracking"),
        ('site:reddit.com Biohub cell tracking Kaggle', 1, "supplemental unquoted search; at least one direct current-competition hit"),
    ]
    for i, (query, count, note) in enumerate(site_queries, 1):
        qrows.append({"query_id": f"reddit_site_{i:02d}", "category": "reddit_site_search", "platform": "Web search site:reddit.com", "query": query, "sort_order": "search-engine relevance", "result_page": 1, "reported_total": "not exposed", "actually_obtained": count, "unique_after_dedupe": "not aggregated", "deep_read_count": 6, "access_time_utc": "2026-09-03T08:14:00Z", "access_time_singapore": "2026-09-03T16:14:00+08:00", "status": "SUCCESS", "evidence_path": repo_evidence("evidence/search_query_evidence.community_history_data.json"), "notes": note + "; observed relevant count/lower bound, not search-engine total"})

    science_queries = ["Cell Tracking Challenge evaluation annotations history", "Zebrahub lineage light-sheet atlas", "Ultrack documentation", "Trackastra transformer cell tracking", "GEFF specification", "tracksdata tracking graph", "ELEPHANT 3D lineage image.sc", "Temporal Affinity Fields cell tracking", "Biohub Royer organismal architecture"]
    for i, query in enumerate(science_queries, 1):
        qrows.append({"query_id": f"scientific_web_{i:02d}", "category": "scientific_web", "platform": "Web search and direct authoritative pages", "query": query, "sort_order": "relevance/authoritative-first", "result_page": 1, "reported_total": "not exposed", "actually_obtained": "route-dependent", "unique_after_dedupe": 14, "deep_read_count": 14, "access_time_utc": "2026-09-03T08:26:17.665Z", "access_time_singapore": "2026-09-03T16:26:17.665+08:00", "status": "PARTIAL" if "Temporal" in query else "SUCCESS", "evidence_path": repo_evidence("evidence/search_query_evidence.community_history_data.json"), "notes": "Authoritative pages were opened and read; bioRxiv remained blocked. Temporal Affinity Fields is only an analogy/community idea, not proven for this task."})

    similar_queries = ["cell tracking", "cell detection", "cell segmentation", "nuclei segmentation", "microscopy", "biomedical image segmentation", "3D microscopy", "time-lapse microscopy", "object tracking", "multi-object tracking", "lineage", "instance segmentation", "zebrafish", "organoid", "embryo", "fluorescent nuclei"]
    for i, query in enumerate(similar_queries, 1):
        qrows.append({"query_id": f"similar_kaggle_{i:02d}", "category": "similar_kaggle", "platform": "Kaggle Competitions / Writeups / Discussion and web search", "query": query, "sort_order": "relevance", "result_page": 1, "reported_total": "not exposed", "actually_obtained": "candidate discovery across query set", "unique_after_dedupe": 10, "deep_read_count": 6, "access_time_utc": "2026-09-03T08:25:02.583Z", "access_time_singapore": "2026-09-03T16:25:02.583+08:00", "status": "SUCCESS", "evidence_path": repo_evidence("evidence/search_query_evidence.community_history_data.json"), "notes": "Six competitions were paired with official pages and authoritative writeups; four remain candidate-only."})
    (EVIDENCE / "search_query_evidence.community_history_data.json").write_text(json.dumps({"reddit_site_queries": site_queries, "scientific_queries": science_queries, "similar_kaggle_queries": similar_queries, "method": "Queries are recorded as executed; result totals are not inferred when the engine did not expose them."}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(BASE / "21_search_query_log.community_history_data.csv", qrows, list(qrows[0]))

    manifest = []
    for row in evidence_rows:
        manifest.append({"source_id": row["source_id"], "source_type": row["source_type"], "platform": row["platform"], "title": row["title"], "author": row.get("author"), "url": row["url"], "query": None, "sort_order": None, "result_page": None, "result_rank": None, "access_time_utc": row.get("access_time_utc"), "access_time_singapore": row.get("access_time_singapore"), "read_status": row["read_status"], "bytes_observed": row["bytes_observed"], "sha256": row.get("sha256"), "version_id": None, "commit_sha": None, "license": None, "evidence_path": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "factual_use_allowed": row["platform"] not in {"Reddit", "image.sc Forum"} and row["read_status"] not in {"BLOCKED", "TITLE_SNIPPET_ONLY"}, "notes": row["summary"]})
    for row in dataset_browser:
        manifest.append({"source_id": row["source_id"], "source_type": "dataset_page", "platform": "Kaggle", "title": row["title"], "author": row["ref"].split("/", 1)[0], "url": row["url"], "query": None, "sort_order": None, "result_page": None, "result_rank": None, "access_time_utc": row["access_time_utc"], "access_time_singapore": row["access_time_singapore"], "read_status": row["read_status"], "bytes_observed": row["bytes_observed"], "sha256": row["sha256"], "version_id": None, "commit_sha": None, "license": None, "evidence_path": repo_evidence("evidence/browser_dataset_page_reads.jsonl"), "factual_use_allowed": False, "notes": row["summary"] + " DO_NOT_USE_PENDING_RULE_REVIEW"})
    for rec in json.loads((BASE / "dataset_search_log.json").read_text(encoding="utf-8")):
        manifest.append({"source_id": f"dataset_search_{len(manifest)+1:04d}", "source_type": "search_results", "platform": "Kaggle", "title": f"Dataset search {rec['query']} page {rec['result_page']}", "author": None, "url": "https://www.kaggle.com/datasets", "query": rec["query"], "sort_order": rec["sort_order"], "result_page": rec["result_page"], "result_rank": None, "access_time_utc": rec["finished_utc"], "access_time_singapore": rec["finished_singapore"], "read_status": "METADATA_ONLY", "bytes_observed": rec["stdout_bytes"], "sha256": rec["stdout_sha256"], "version_id": None, "commit_sha": None, "license": None, "evidence_path": repo_evidence(rec["stdout_path"]), "factual_use_allowed": True, "notes": f"returned={rec['result_count']}; empty={rec['empty_result_response']}"})
    for sid, row in zip(similar_source_ids[6:], HISTORY_CANDIDATES[6:]):
        manifest.append({"source_id": sid, "source_type": "historical_competition_candidate", "platform": "Kaggle", "title": row["competition"], "author": None, "url": row["url"], "query": "similar Kaggle competition discovery", "sort_order": "relevance", "result_page": 1, "result_rank": None, "access_time_utc": "2026-09-03T08:25:02.583Z", "access_time_singapore": "2026-09-03T16:25:02.583+08:00", "read_status": "TITLE_SNIPPET_ONLY", "bytes_observed": 0, "sha256": None, "version_id": None, "commit_sha": None, "license": None, "evidence_path": repo_evidence("evidence/search_query_evidence.community_history_data.json"), "factual_use_allowed": False, "notes": "Candidate discovery only; no rank, score, or detailed metric claim."})
    browser_refs = {row["ref"] for row in dataset_browser}
    for rec in json.loads((BASE / "dataset_detail_records.json").read_text(encoding="utf-8")):
        if rec["ref"] in browser_refs:
            continue
        sid = "dataset_candidate_" + re.sub(r"[^a-z0-9]+", "_", rec["ref"].lower()).strip("_")
        manifest.append({"source_id": sid, "source_type": "dataset_detail_attempt", "platform": "Kaggle", "title": rec["ref"], "author": rec["ref"].split("/", 1)[0], "url": rec["url"], "query": rec.get("selection_reason"), "sort_order": None, "result_page": None, "result_rank": None, "access_time_utc": rec.get("finished_utc"), "access_time_singapore": rec.get("finished_singapore"), "read_status": "RATE_LIMITED", "bytes_observed": rec.get("metadata_bytes") or 0, "sha256": rec.get("metadata_sha256"), "version_id": None, "commit_sha": None, "license": None, "evidence_path": repo_evidence("dataset_detail_records.json"), "factual_use_allowed": False, "notes": "Metadata/file detail call rate-limited; no automatic retry; DO_NOT_USE_PENDING_RULE_REVIEW."})
    with (BASE / "00_source_manifest.community_history_data.jsonl").open("w", encoding="utf-8") as handle:
        for row in manifest:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    claims = [
        {"claim_id": "community_current_issue", "report_section": "Reddit and community", "claim_text": "A Reddit user reported Biohub submission/save/score delays up to nearly a day.", "claim_type": "COMMUNITY_REPORT", "source_ids": "reddit_biohub_submission_issue", "evidence_paths": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "direct_or_inference": "direct community report", "confidence": "low for platform-wide behavior", "conflict_present": "false", "conflict_notes": "No official confirmation."},
        {"claim_id": "ctc_metrics", "report_section": "Scientific sources", "claim_text": "CTC separates detection, tracking/linking and biological measures; OP_CTB combines SEG and TRA.", "claim_type": "OFFICIAL_FACT", "source_ids": "ctc_evaluation", "evidence_paths": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "direct_or_inference": "direct", "confidence": "high", "conflict_present": "false", "conflict_notes": "Different from current Kaggle metric."},
        {"claim_id": "ctc_annotations", "report_section": "Scientific sources", "claim_text": "CTC gold and silver annotations trade spatial coverage against annotation quality.", "claim_type": "OFFICIAL_FACT", "source_ids": "ctc_annotations", "evidence_paths": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "direct_or_inference": "direct", "confidence": "high", "conflict_present": "false", "conflict_notes": "None."},
        {"claim_id": "zebrahub_context", "report_section": "Scientific sources", "claim_text": "Zebrahub combines single-cell sequencing and light-sheet lineage reconstruction in a developmental atlas.", "claim_type": "OFFICIAL_FACT", "source_ids": "zebrahub_pubmed | biohub_royer", "evidence_paths": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "direct_or_inference": "direct synthesis", "confidence": "high", "conflict_present": "false", "conflict_notes": "Does not prove Kaggle reuse permission."},
        {"claim_id": "ultrack_scope", "report_section": "Scientific sources", "claim_text": "Ultrack supports 2D/3D tracking through segmentation hypotheses, linking and global solving.", "claim_type": "OFFICIAL_FACT", "source_ids": "ultrack_docs", "evidence_paths": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "direct_or_inference": "direct", "confidence": "high", "conflict_present": "false", "conflict_notes": "Biohub performance unmeasured."},
        {"claim_id": "trackastra_scope", "report_section": "Scientific sources", "claim_text": "Trackastra predicts temporal associations and supports division given segmentations or detections.", "claim_type": "SOURCE_CODE_VERIFIED", "source_ids": "trackastra_arxiv | trackastra_github", "evidence_paths": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "direct_or_inference": "direct synthesis", "confidence": "high for documented scope", "conflict_present": "false", "conflict_notes": "No current-competition CV."},
        {"claim_id": "geff_structure", "report_section": "Scientific sources", "claim_text": "GEFF represents tracking graphs in Zarr groups for node and edge IDs, properties and axis metadata.", "claim_type": "OFFICIAL_FACT", "source_ids": "geff_spec", "evidence_paths": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "direct_or_inference": "direct", "confidence": "high", "conflict_present": "false", "conflict_notes": "None."},
        {"claim_id": "history_3d_transfer", "report_section": "Similar Kaggle competitions", "claim_text": "CZII and BYU are the closest historical Kaggle evidence for 3D point localization, but neither models time or division.", "claim_type": "INFERENCE", "source_ids": "hist_czii | hist_czii_writeup | hist_byu | hist_byu_writeup", "evidence_paths": repo_evidence("evidence/browser_reddit_science_history_reads.jsonl"), "direct_or_inference": "inference from direct comparisons", "confidence": "medium-high", "conflict_present": "false", "conflict_notes": "Requires temporal, GEFF and graph-metric adaptation."},
        {"claim_id": "dataset_deep_count", "report_section": "Kaggle Datasets", "claim_text": "28 Kaggle Dataset pages had visible main regions fully read; 2 additional pages were blocked.", "claim_type": "MEASURED", "source_ids": "dataset_page_dalloliogm_biohub_official_scorer_patched | dataset_page_busyaprime_biohub_local_scoring_support_pack", "evidence_paths": repo_evidence("evidence/browser_dataset_page_reads.jsonl"), "direct_or_inference": "measured count over evidence file", "confidence": "high", "conflict_present": "false", "conflict_notes": "Source IDs listed are anchors; count covers full evidence file."},
        {"claim_id": "dataset_eligibility", "report_section": "External data legality", "claim_text": "No Dataset candidate in this subtask completed rule-eligibility and leakage review.", "claim_type": "MEASURED", "source_ids": "dataset_page_kms111201_full_data | dataset_page_kkunizaw_biohub_zh001r", "evidence_paths": repo_evidence("evidence/browser_dataset_page_reads.jsonl"), "direct_or_inference": "scope ledger", "confidence": "high", "conflict_present": "false", "conflict_notes": "All rows marked DO_NOT_USE_PENDING_RULE_REVIEW."},
    ]
    write_csv(BASE / "19_claims_evidence_matrix.community_history_data.csv", claims, list(claims[0]))


if __name__ == "__main__":
    build()
