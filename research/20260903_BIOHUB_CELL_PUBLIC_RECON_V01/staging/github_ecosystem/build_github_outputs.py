#!/usr/bin/env python3
"""Build merge-ready GitHub research drafts from read-only evidence.

All outputs remain inside this staging directory.  No network or Git write is
performed here; this script only transforms already captured query/deep-read
evidence into CSV, Markdown, and JSONL drafts.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"
REPO_REL_ROOT = Path("research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/github_ecosystem")
ACCESS_WINDOW = "2026-09-03T08:19:00Z..2026-09-03T08:25:00Z"


def names(text: str) -> list[str]:
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


def repo_rel(path: Path | str) -> str:
    local = Path(path)
    if local.is_absolute():
        local = local.relative_to(ROOT)
    return str(REPO_REL_ROOT / local)


def singapore_time(value: str) -> str:
    if ".." in value:
        start, end = value.split("..", 1)
        return singapore_time(start) + ".." + singapore_time(end)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone(timedelta(hours=8))).isoformat()


def page(label: str, query_id: str, number: int, total: int, byte_count: int, digest: str, repo_text: str) -> dict:
    return {
        "source_id": f"GH-SEARCH-{label}",
        "query_id": query_id,
        "page": number,
        "reported_total": total,
        "bytes": byte_count,
        "sha256": digest,
        "repos": names(repo_text),
    }


REPO_SEARCH_PAGES = [
    page("EXACT-P1", "GH-RS-001", 1, 37, 1995, "59b28a9a8c2f50a01ee55c8dc45571f5118db2330aae8f63c4d0e70bb5d48cdb", """
vitalclick/Biohub
tanvik7072/Biohub-Cell-Tracking-During-Development
phucthaiv02/biohub-cell-tracking
gluzdovds-wq/Biohub---Cell-Tracking-During-Development
Tobi-joshua/Biohub---Cell-Tracking-During-Development
vicky0718/Biohub-Cell_Tracking_During_Development
mybenkhadda/Biohub---Cell-Tracking-During-Development
Sumant40/Biohub---Cell-Tracking-During-Development
barbo0909/Biohub---Cell-Tracking-During-Development
vaishnavi-ctrl-jpg/Biohub-Cell-Tracking-During-Development
"""),
    page("EXACT-P2", "GH-RS-001", 2, 37, 2210, "18ec15029d3e70aa6480316619576f79233a35d269178b37fa9760fff76b807f", """
homeshwarnelakurthi/Biohub---Cell-Tracking-During-Development
chaitanyajamble/Biohub---Cell-tracking-during-development
gano0802/Biohub---Cell-Tracking-During-Development
Md-Ali-Azad/Biohub---Cell-Tracking-During-Development
AndreDon0/Biohub---Cell-Tracking-During-Development-Solution
leooooeo/Biohub---Cell-Tracking-During-Development-unet
kito2718/kaggle_Biohub-Cell_Tracking_During_Development
tuannm3812/kaggle-biohub-cell-tracking-during-development
Binyx5/biohub-cell-tracking
jsphyg/biohub-cell-tracking-kaggle
"""),
    page("EXACT-P3", "GH-RS-001", 3, 37, 2384, "ac09a763d0760cb6cca9f52d1daf79e588d5d8617099af23a61197a9d7160659", """
kito2718/kaggle_Biohub-Cell_Tracking_During_Development2
sota1111/biohub-claude
sota1111/biohub-gpt
SailorRen/Biohub-CELL
oivler/biohub-cell-tracking
HOnO726/kaggle_biohub
ovationtox-ym/Cell-Tracking
pjazzy314159/biohub
matt-ceran/biohub-cell-tracking
m9h/biohub-starter
"""),
    page("EXACT-P4", "GH-RS-001", 4, 37, 2431, "cbc0792070370eaf494ddec821027ad7edb3f0317d4cbbf3d246784bf8103df0", """
ratishgurav/biohub-cell-tracking
tarunn613/biohub-cell-tracking
JunhaoLiXD/Biohub_Cell_Tracking
Padmavathi-S-code/Kaggle_Biohub_Learning_Journal
Hugodevpro/BioHub-Cell-Tracking-computer-vision
drosadocastro-bit/Atabey
ytashan/Bio-Cell-Exploratory-Data-Analysis-EDA-
"""),
    page("BROAD-P1", "GH-RS-002", 1, 68, 1996, "d9efb2ebba1144b2595575cf7c3e32d1c4d67dae5ddd797648bbb9a40a2b9bf5", """
vitalclick/Biohub
tanvik7072/Biohub-Cell-Tracking-During-Development
phucthaiv02/biohub-cell-tracking
Beiciccc/biohub-cell-tracking-development
Binyx5/biohub-cell-tracking
jsphyg/biohub-cell-tracking-kaggle
kito2718/kaggle_Biohub-Cell_Tracking_During_Development
ranjithsnair74/biohub-cell-tracking
sota1111/biohub-claude
AyonDandapath/-biohub-cell-tracking.
"""),
    page("BROAD-P2", "GH-RS-002", 2, 68, 2363, "89487c4d1a8bb6d876d1928eb35e1e24c34b7a0b331e10aa3a68590b6d2766af", """
oshbocker/biohub_cell_tracking
sota1111/biohub-gpt
melani-maheswaran/biohub-cell-tracking
Adisaok/biohub-cell-tracking
asapacsin/biohub-cell-tracking
Dhanushach126/Biohub-Cell-Tracking
matt-ceran/biohub-cell-tracking
oivler/biohub-cell-tracking
drissou-milad/biohub-cell-tracking
ratishgurav/biohub-cell-tracking
"""),
    page("BROAD-P3", "GH-RS-002", 3, 68, 2404, "a0df27066b398f9065ce94c665fe34e304c3a354bc59199bbf4a57780ce94c4e", """
pomagrenate/biohub-cell-tracking
tarunn613/biohub-cell-tracking
JunhaoLiXD/Biohub_Cell_Tracking
SurehSan/Biohub---Cell-Tracking
ZitouniNidhal/biohub-cell-tracking
pathik1511/biohub-cell-tracking
KabiththananParan/biohub-cell-tracking
sidetech311-hash/-Biohub-Cell-Tracking
georgesmiley-ut/biohub-cell-tracking
Santosdevbjj/biohub-cell-tracking
"""),
    page("BROAD-P4", "GH-RS-002", 4, 68, 1762, "f6ee2a23719d433df02fe981dadc5bc3ab4d422a43d58c185d1626c7b8c960f0", """
tanushm31/biohub-cell-tracking
manikmayur/biohub-cell-tracking
AshutoshBiswal26/Biohub-Cell-Tracking
Sarahnjunge/biohub-cell-tracking
AskChristopher/biohub-cell-tracking
Shubhranshu331/Biohub-Cell-Tracking
szymonczaja/Biohub-cell-tracking
AnhDucVu-Hust/Biohub_Cell_Tracking
AgostinhoS/KAGGLE---Biohub-Cell-Tracking
kito2718/kaggle_Biohub-Cell_Tracking_During_Development2
"""),
    page("BROAD-P5", "GH-RS-002", 5, 68, 2007, "6ac710b0b943b3e744a426a2f70dc195800bd2000dbc5f45bf6da9d2ef570bc0", """
DarkHeian/biohub-cell-tracking-visualizer
TejasThate/kaggle-biohub-cell-tracking
SailorRen/Biohub-CELL
gluzdovds-wq/Biohub---Cell-Tracking-During-Development
Tobi-joshua/Biohub---Cell-Tracking-During-Development
mybenkhadda/Biohub---Cell-Tracking-During-Development
vicky0718/Biohub-Cell_Tracking_During_Development
Sumant40/Biohub---Cell-Tracking-During-Development
Kai-Gowers/biohub-cell-tracking-v2
codaxo-ai/Biohub-Cell-Tracking-During-Developmen
"""),
    page("BROAD-P6", "GH-RS-002", 6, 68, 2037, "b45c67a8de95edc4707d1adc00370402de11ca34efb197c8b319aa8478e1ef6f", """
willlaon/biohub-cell-tracking-graph-learning
barbo0909/Biohub---Cell-Tracking-During-Development
chaitanyajamble/Biohub---Cell-tracking-during-development
gano0802/Biohub---Cell-Tracking-During-Development
Md-Ali-Azad/Biohub---Cell-Tracking-During-Development
homeshwarnelakurthi/Biohub---Cell-Tracking-During-Development
vaishnavi-ctrl-jpg/Biohub-Cell-Tracking-During-Development
AndreDon0/Biohub---Cell-Tracking-During-Development-Solution
HOnO726/kaggle_biohub
ovationtox-ym/Cell-Tracking
"""),
    page("BROAD-P7", "GH-RS-002", 7, 68, 2482, "a39a49f1a262095df302dff1ba1105474d93ca7e61cecc9620120e1d3f25c02c", """
leooooeo/Biohub---Cell-Tracking-During-Development-unet
tuannm3812/kaggle-biohub-cell-tracking-during-development
pjazzy314159/biohub
m9h/biohub-starter
Padmavathi-S-code/Kaggle_Biohub_Learning_Journal
Hugodevpro/BioHub-Cell-Tracking-computer-vision
drosadocastro-bit/Atabey
ytashan/Bio-Cell-Exploratory-Data-Analysis-EDA-
"""),
    page("KAGGLE-P1", "GH-RS-003", 1, 28, 2033, "e4b1d9ef1a7aea6c1efc73682665ea3b04296d4c64b017dca81f2eb33c262198", """
vdeeplearning/biohub_kaggle_cell_tracking
Beiciccc/biohub-cell-tracking-development
SurehSan/Biohub---Cell-Tracking
jsphyg/biohub-cell-tracking-kaggle
Binyx5/biohub-cell-tracking
sota1111/biohub-claude
kito2718/kaggle_Biohub-Cell_Tracking_During_Development
ranjithsnair74/biohub-cell-tracking
sota1111/biohub-gpt
HOnO726/kaggle_biohub
"""),
    page("KAGGLE-P2", "GH-RS-003", 2, 28, 2607, "954bdd25e52599be28b151d61559d9e9f3b3988f5ee36490008ffdf3b6ce593a", """
szymonczaja/Biohub-cell-tracking
AgostinhoS/KAGGLE---Biohub-Cell-Tracking
SailorRen/Biohub-CELL
oivler/biohub-cell-tracking
TejasThate/kaggle-biohub-cell-tracking
kito2718/kaggle_Biohub-Cell_Tracking_During_Development2
drissou-milad/biohub-cell-tracking
Kukomoo/cell-tracking-biohub
matt-ceran/biohub-cell-tracking
tuannm3812/kaggle-biohub-cell-tracking-during-development
"""),
    page("KAGGLE-P3", "GH-RS-003", 3, 28, 2416, "e899e5a679209bc5f4417ba18fa66d7730073f50946e594a09fddd93c853f163", """
ovationtox-ym/Cell-Tracking
tarunn613/biohub-cell-tracking
JunhaoLiXD/Biohub_Cell_Tracking
ratishgurav/biohub-cell-tracking
Aswin20122005/cell-tracking-3d
m9h/biohub-starter
Padmavathi-S-code/Kaggle_Biohub_Learning_Journal
drosadocastro-bit/Atabey
"""),
    page("ULTRACK-P1", "GH-RS-004", 1, 21, 1985, "73070ca2cc1eda9dae17d66d51fcd00f6db5580f3a0b2f623e7af0501a0b56e3", """
royerlab/ultrack
royerlab/ultrack-td
christopherstj/ultrack
johnlampa/ultrack
dieultrack/ultrack
royerlab/ultrack-i2k2023
royerlab/ultrack-i2k2024
royerlab/ultrack_supplementary
royerlab/ultrack-imagej
christopherstj/ultrack-cloud-resources
"""),
    page("ULTRACK-P2", "GH-RS-004", 2, 21, 2110, "1567cc73883fd3ad7f2d0f3c84c68b6cf229fea0eae6a63655966437a8e2aa5e", """
jazmin-sha/ULTracker
tabonsiktir-stack/Ultracker
ReyDocs/ultrack_alltrack
Myrto-Bioinfo-Lab/Tribolium-Ultrack
henryyantq/Ultrack_experimental
jazmin-sha/ulTrackHero
ultracker-lester/ultracker-lester
jackyko1991/Ultrack-Cluster
royerlab/ultrack_CTC_submission
royerlab/ultrack-atini-2025
"""),
    page("ULTRACK-P3", "GH-RS-004", 3, 21, 888, "b68668af74a4839ef1e905cf7816867d4f75fa19a8987b8cb13328677022b775", "vincent-tvincent/ultrack_experiment_yp"),
    page("TRACKASTRA-P1", "GH-RS-005", 1, 12, 1695, "2172c1451b2e9208b1d5b7fc978351eed1896acd26b65db414bec523fa40f6dc", """
weigertlab/trackastra
weigertlab/napari-trackastra
conda-forge/trackastra-feedstock
C-Achard/Trackastra-et-Ultra
trackmate-sc/TrackMate-Trackastra
Danielbb14/TrackastraTestTB
MIDL26-Short-Tracking/trackastra_y
helalabcd/trackastrassl
bioinfbrad/trackastra-galaxy
cdalinghaus-mthesis/trackastra_x
"""),
    page("TRACKASTRA-P2", "GH-RS-005", 2, 12, 1033, "7d99ee821ac8ded257d5aa002c293b9e76361ccab46ab5a7f67689c2738c8b40", """
weigertlab/trackastra-models
jamila-griffith/Tracking_OECs-Using-Trackastra-
"""),
    page("GEFF", "GH-RS-006", 1, 4, 1215, "4e359895bcda72b9c8bde7b48f01dec00d5ea6c930a889e273a2d0a7d2d25a24", """
live-image-tracking-tools/geff
live-image-tracking-tools/napari-geff
live-image-tracking-tools/geff-java
live-image-tracking-tools/geff-js-validator
"""),
    page("ZEBRAHUB", "GH-RS-007", 1, 8, 1722, "0ac6807f42f3827fbf8e8e2dc5c37296b483a2c7a22e16df7bab2927ea8170cb", """
czbiohub-sf/zebrahub_analysis
royerlab/zebrahub-paper-umap-3d
czbiohub-sf/zebrahub-multiome-analysis
royerlab/zebrahub-protocols
royerlab/zebrahub-napari-animation
vitor458105/ZebraHub
Tha1s24/Projeto_ZebraHub
royerlab/zebrahub-paper-hcr-analysis
"""),
    page("ROYER", "GH-RS-008", 1, 5, 1500, "43c82f7baf03871d9c5522aae1124870cc39ffadaa9222f5c117f1fb9d3917aa", """
royerlab/ultrack
royerlab/kaggle-cell-tracking-competition
royerlab/inTRACKtive
royerlab/tracksdata
royerlab/trackedit
"""),
    page("CTC-P1", "GH-RS-009", 1, 33, 2403, "96bd5359418bdf5b1c60e7af9ad3de9390db9e6ecdb7e2b53941f119167f5381", """
s-shailja/ucsb_ctc
amirfaraji/CellTracking
CellTrackingChallenge/CTC-FijiPlugins
CIVA-Lab/U-SE-ResNet-for-Cell-Tracking-Challenge
TimScherr/KIT-GE-3-Cell-Segmentation-for-CTC
Nutlope/cell-tracking-viz
RSuchkov32/Cell-Tracking-Challenge
trackmate-sc/TrackMate-CTCRunner
oyishyi/Cell-Tracking-Challenge-CTC-
robertorojasp06/ctc-submissions
"""),
    page("CTC-P2", "GH-RS-009", 2, 33, 2404, "67776657dd21a1dfcf7f9d8abc873382546902b38a51ecd360365cef7fc8efc4", """
Thenowolf/Cell-tracking-challenge
sydneycally-inclane-2812/cell-tracking-challenge-cv-project
robertorojasp06/ctc-drosophila-other-models
ksugar/CTC-IGFL-FR
most-ieeta/Cell-tracking-challenge
Nakshu/Cell-Tracking-Challenge
taresh18/Cell-Tracking-Challenge
BIBIyi/Cell-Tracking-Challenge--CTC-
ksugar/elephant-ctc
mcha0019/Cell-Detection-and-Segmentation
"""),
    page("CTC-P3", "GH-RS-009", 3, 33, 2765, "2aa138b46acb695c81b71de53e4a851a27afd915255b9ae15db4c61632e12eee", """
PlaceboPaul/cell_seg_n_track
AbigailMcGovern/CTC-data-wrangling
gabrielribcesario/DIC-C2DH-Hela
OlaDare247/Medical-Imaging-----VISTA2D-MONAI
syucat/Tymdigk_CTModel
JorgeArguello1999/U-Net
David-Ciz/label-fusion-ng-fork
tink0mar/yolo_sam2_cell_tracker
ashkr318/ML-U-Net-project
Amit-Brilant/cell-segmentation-byol-unet
"""),
    page("CTC-P4", "GH-RS-009", 4, 33, 1577, "8822c4c3abb6f93f3c3b8a99d586d8738f93a177c9cb273955c6059ea8767380", """
OtoYuki/cell_tracking
OlaDare247/maskrcnn_ctc
rima-dev/U-Net-Convolutional-Networks-for-Biomedical-Image-Segmentation
"""),
    page("ZEBRA-KAGGLE", "GH-RS-010", 1, 7, 2347, "7cf3fcfd28a9b4be905f45bce5f4a26011632e2e55549e224985af47093a016e", """
AkilsuryaS/Kaggle-Biohub
drissou-milad/biohub-cell-tracking
matt-ceran/biohub-cell-tracking
AntonioTagliatti/BioHub
tuannm3812/kaggle-biohub-cell-tracking-during-development
tarunn613/biohub-cell-tracking
ratishgurav/biohub-cell-tracking
"""),
    page("ULTRACK-ZEBRA", "GH-RS-011", 1, 1, 1007, "ae09c603676bd8d181e7325d27416d733163f77932430cd20f3fe6af3031724c", "ayse-nur-safak/Detecting-Linking-and-Reconstructing-Cell-Lineages-in-3D-Time-Zebrafish-Microscopy"),
    page("GRAPH-OPT", "GH-RS-012", 1, 1, 1005, "b02c5e0d73c423f5d9e8e4f98fc190256cba3853d45dc2bd4249892b1628b091", "pomagrenate/biohub-cell-tracking"),
    page("TRACKSDATA-P1", "GH-RS-013", 1, 144, 1716, "ebbb8b5bf1ac888bf0d055b4894e55e9aff3d717f64b09657fe8d9c51d36d13a", """
royerlab/tracksdata
tracksdata/CTS-Fullstack-Pune
tracksdata/scb-microservices
tracksdata/mef-cambodia
tracksdata/Cognizant-JAVA-FSD-HYD
tracksdata/OSP-React
tracksdata/cde-cognizant
tracksdata/Cognizant-IIT-CHN
tracksdata/cts-adm-microservices
tracksdata/steerbatch7-cloud
"""),
]


ZERO_REPO_SEARCHES = [
    ("GH-RS-014", "org:czbiohub-sf tracking", 485, "cbd84c2d10e645129b6c56f13ad002dcc77d79fbfa42e2724b99746f39525309"),
    ("GH-RS-015", "GEFF tracksdata Biohub", 429, "e141fd64b1fe0d5053b638b2c8087da5e334329e7881fb540812d5bad25abefc"),
    ("GH-RS-016", "adjusted_edge_jaccard", 428, "f86c3c059ed1f070af25438075e019bd43136ac030444ac098e69b1a15c8319e"),
    ("GH-RS-017", "division_jaccard Biohub", 430, "36c51c395ad863954a499ecbbd9020ece4c654bc026c3562c9b1ab73c6531d29"),
    ("GH-RS-018", '"temporal affinity fields" cell lineage', 446, "efa36c3028ddfb4ca6e6b41453de3531f2b164c35440fe79271ce568067a0636"),
    ("GH-RS-019", "OME-Zarr zebrafish tracking", 434, "67ea1b7e2d02637035bac739d6554babad2898374a9984352bc380a6a9bb2df5"),
]


QUERY_DEFS = {
    "GH-RS-001": ('"biohub-cell-tracking-during-development"', 4, 37, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-002": ('"Biohub Cell Tracking"', 7, 68, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-003": ('"Biohub" "cell tracking" Kaggle', 3, 28, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-004": ("ultrack in:name", 3, 21, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-005": ("trackastra in:name", 2, 12, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-006": ("geff in:name tracking", 1, 4, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-007": ("zebrahub", 1, 8, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-008": ("org:royerlab tracking", 1, 5, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-009": ('"Cell Tracking Challenge"', 4, 33, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-010": ("zebrafish 3D cell tracking kaggle", 1, 7, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-011": ("Ultrack zebrafish embryo", 1, 1, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-012": ("graph optimization cell lineage", 1, 1, "COMPLETE_ALL_REPORTED_PAGES"),
    "GH-RS-013": ("tracksdata in:name", 1, 144, "PARTIAL_PAGE_1_ONLY_NAME_COLLISION_DOMINATED"),
}


CODE_SEARCHES = [
    ("GH-CS-001", "biohub-cell-tracking-during-development", 100, 20, 7702, "62b9fca436ec98bdea873d06471914b0f71b4bbc1f9a9f12cb08dc50c6570b82"),
    ("GH-CS-002", "adjusted_edge_jaccard", 101, 21, 7318, "3741879a69ad23ff66cb5bcd289ba5247319bf36c9d86a321e7dac2be1287cfd"),
    ("GH-CS-003", "division_jaccard Biohub", 100, 20, 11018, "67dfaba067710732ed1ff914d3c1404457af2077c9f90c7f9034bbcc461fa7e4"),
    ("GH-CS-004", "GEFF tracksdata Biohub", 100, 20, 12896, "e3fd86f095d5267a09e30c270d55d1ce721d856735d5507aed5a3dc0251a8d64"),
    ("GH-CS-005", '"temporal affinity fields" cell lineage', 165, 2, 1525, "ad6d0b9c362042639cc1e394aff38190a538e4541753ac8f31b8ef337141066e"),
    ("GH-CS-006", "OME-Zarr zebrafish tracking", 128, 36, 13408, "7515de7f643121b70e18f356a6fa5a66b7db99ab384591fc8cfea3e9d4a62953"),
    ("GH-CS-007", "Ultrack zebrafish embryo", 74, 24, 13405, "c8d4f9852855e105cf60d699d16603f58fc56eafda2b72cb6dda3081cd8deedf"),
    ("GH-CS-008", "Trackastra cell tracking", 139, 27, 12426, "6ba9e3ab4fddd50fc1ccbae4414d5ba4093ba3961110c9f2cfea05f963782e06"),
    ("GH-CS-009", "graph optimization cell lineage", 151, 45, 13118, "f696a3ae9bc117e7f54e777ba2ad63f01ebaea998ba3a5586471320c66602256"),
]


CODE_REPOS = names("""
dalloliogm/kaggle_competitions
seshurajup/myclew
phucthaiv02/biohub-cell-tracking
sota1111/biohub-gpt
tossowski/BioHub
drosadocastro-bit/Atabey
AndreDon0/Biohub---Cell-Tracking-During-Development-Solution
kevzho/kaggle-comps
victornguyen7/celltrack3d
ZitouniNidhal/ZebraTrack3D
Rudolf-Staline/biohub-cell-tracker
Borda/kaggle_tracking
Dnyanesh-29/Cell-Tracking-During-Development
royerlab/kaggle-cell-tracking-competition
adrianomartinelli/kaggle-cell-tracking-competition
NotShubham1112/Detect-and-track-zebrafish-cells-through-3D-space-and-time
naveenlx111-svg/Biohub
Jin-Ruoting/Cell-Tracking-During-Development
Bioinfo-Rafael/biohub
AntonioTagliatti/BioHub
FaisalTabrez/Kaggle_Bio
pr4deepr/biohub-trackviz
ome/ngff
czbiohub-sf/shrimPy
royerlab/ultrack_supplementary
computational-cell-analytics/cochlea-net
royerlab/ultrack
m9h/biohub-starter
MercaderLabAnatomy/T-MIDAS
cellseek/gui
trackmate-sc/TrackMate-Trackastra
SchmollerLab/Cell_ACDC
Kapoorlabs-CAPED/KapoorLabs-Lightning
""")


WEB_QUERIES = [
    ("GH-WEB-001", "site:github.com/royerlab cell tracking Ultrack tracksdata GEFF", "royerlab/ultrack;royerlab/tracksdata;royerlab/inTRACKtive"),
    ("GH-WEB-002", 'site:github.com "Biohub - Cell Tracking During Development" Kaggle', "matt-ceran/biohub-cell-tracking;royerlab/kaggle-cell-tracking-competition"),
    ("GH-WEB-003", "site:github.com Cell Tracking Challenge software repository", "CellTrackingChallenge/CTC-FijiPlugins;CellTrackingChallenge/py-ctcmetrics"),
    ("GH-WEB-004", "site:github.com Trackastra cell tracking", "weigertlab/trackastra;weigertlab/napari-trackastra"),
    ("GH-WEB-005", "site:github.com/royerlab tracksdata geff", "royerlab/tracksdata;live-image-tracking-tools/geff"),
    ("GH-WEB-006", "site:github.com/live-image-tracking-tools geff", "live-image-tracking-tools/geff;live-image-tracking-tools/geff-java;live-image-tracking-tools/napari-geff"),
    ("GH-WEB-007", "site:github.com zebrahub tracking royerlab", "czbiohub-sf/zebrahub_analysis;royerlab/zebrahub-paper-umap-3d"),
    ("GH-WEB-008", "site:github.com temporal affinity fields cell tracking", "elephant-track/elephant-server"),
    ("GH-WEB-009", '"Temporal Affinity Fields" GitHub cell tracking', "elephant-track/elephant-server"),
    ("GH-WEB-010", "site:github.com ELEPHANT cell tracking temporal affinity fields", "elephant-track/elephant-server;ksugar/elephant-ctc"),
    ("GH-WEB-011", "site:github.com 3DeeCellTracker cell tracking", "WenChentao/3DeeCellTracker"),
    ("GH-WEB-012", "site:github.com Cellpose cell tracking lineage", "MouseLand/cellpose"),
]


STARS = {
    "royerlab/kaggle-cell-tracking-competition": (62, 15),
    "royerlab/tracksdata": (14, 7),
    "live-image-tracking-tools/geff": (42, 13),
    "royerlab/ultrack": (207, 30),
    "weigertlab/trackastra": (149, 32),
    "CellTrackingChallenge/py-ctcmetrics": (33, 6),
    "CellTrackingChallenge/2021-edition-available-colabs": (11, 1),
    "WenChentao/3DeeCellTracker": (70, 11),
    "quantumjot/btrack": (335, 55),
    "raphaelreme/byotrack": (24, 6),
    "matt-ceran/biohub-cell-tracking": (0, 0),
    "tarunn613/biohub-cell-tracking": (0, 0),
    "phucthaiv02/biohub-cell-tracking": (0, 0),
    "sota1111/biohub-claude": (0, 0),
    "tossowski/BioHub": (0, 0),
    "m9h/biohub-starter": (1, 1),
    "elephant-track/elephant-server": (9, 6),
    "MouseLand/cellpose": (2300, 644),
    "live-image-tracking-tools/geff-java": (2, 0),
}


def method(
    role: str,
    detection: str,
    segmentation: str,
    temporal_linking: str,
    division: str,
    optimization: str,
    training: str,
    inference: str,
    evaluation: str,
    data_io: str,
    submission: str,
    postprocessing: str,
    key_finding: str,
) -> dict:
    return {
        "role": role,
        "detection": detection,
        "segmentation": segmentation,
        "temporal_linking": temporal_linking,
        "division_handling": division,
        "optimization": optimization,
        "training": training,
        "inference": inference,
        "evaluation": evaluation,
        "data_io": data_io,
        "submission": submission,
        "postprocessing": postprocessing,
        "key_finding": key_finding,
    }


METHODS = {
    "royerlab/kaggle-cell-tracking-competition": method(
        "competition host baseline", "TemporalUNet3D predicts per-voxel cell-center probabilities; physical-space NMS extracts nodes", "N/A: point centers rather than instance masks",
        "SimpleNodeTransformer scores cross-frame node pairs from image features plus relative 3D coordinates; sliding windows and greedy parent/child-constrained solve, with optional ILP path",
        "allows at most two children; dedicated sparse-annotation-aware division scoring and bipartite pairing prevent double credit", "greedy constrained selection or optional global ILP",
        "voxel target + edge BCE restricted to annotated active rows/columns; unannotated sparse regions ignored", "0.1/99.9 quantile normalization, overlapping time windows, optional XY-flip TTA, physical NMS",
        "node matching within physical radius; adjusted edge Jaccard plus division Jaccard", "OME-Zarr input; tracksdata/GEFF graph output", "GEFF-to-CSV and CSV-to-GEFF scripts", "candidate thresholding, NMS, graph constraint solve",
        "mandatory starting point and the closest reproducible reference implementation for the competition metric and submission path",
    ),
    "royerlab/tracksdata": method(
        "graph data/model toolkit", "N/A", "N/A", "KDTree distance candidate edges; nearest-neighbor and ILP solvers", "max_children constraint and explicit shift_division utilities",
        "greedy edge ordering or ilpy flow-conservation ILP with appearance/disappearance/division variables", "N/A", "library API", "distance matching, CTC/traccuracy adapters", "SQL/network graph backends and GEFF read/write/repair", "N/A", "graph transforms",
        "important reusable graph layer, but not a detector or end-to-end competition solution",
    ),
    "live-image-tracking-tools/geff": method(
        "interchange format reference", "N/A", "N/A", "N/A", "track validation checks graph semantics; no tracker", "N/A", "N/A", "read/write/conversion API",
        "schema and graph/track validation", "Zarr-backed GEFF, schema, NetworkX/rustworkx adapters, CTC conversion", "CTC conversion only; not Kaggle submission assembly", "validation/normalization only",
        "GEFF is an interoperability substrate, not a tracking algorithm",
    ),
    "royerlab/ultrack": method(
        "general 2D/3D tracker", "expects foreground/contour evidence from upstream models", "hierarchical oversegmentation proposes mutually exclusive segment candidates",
        "KDTree spatial candidates with motion/color features", "binary division variable in global biological flow constraints", "mixed-integer program; Gurobi when available with CBC fallback",
        "N/A for a fixed detector; tracking parameters configured", "segment -> link -> solve pipeline", "export/CTC support, no competition adjusted-Jaccard evaluator in selected core", "SQLite working DB and GEFF export", "GEFF and CTC exports", "global selection resolves overlapping segments and track links",
        "particularly relevant because its tree includes a Zebrahub example and joint segmentation/tracking optimization",
    ),
    "weigertlab/trackastra": method(
        "learned association tracker", "N/A: consumes instance masks", "upstream instance segmentation required",
        "transformer predicts association matrix from object coordinates, region/image features, and time windows", "greedy mode supports divisions; greedy_nodiv disables them; ILP mode available", "greedy or ILP graph selection",
        "training script builds windows and association supervision", "pretrained 2D/3D models; predicts candidates then applies graph solver", "tracking graph outputs; no native Biohub metric", "TIFF images + label masks", "N/A native Kaggle converter", "applies solved graph to masks",
        "strong association component but requires a segmentation/front-end and Biohub-format bridge",
    ),
    "CellTrackingChallenge/py-ctcmetrics": method(
        "evaluation toolkit", "N/A", "N/A", "N/A", "BC and CHOTA lineage-aware evaluation", "N/A", "N/A", "CLI evaluates result directories",
        "DET, SEG, TRA, LNK, HOTA, CHOTA and validation", "CTC masks + res_track.txt/man_track.txt", "N/A", "merges track representations for metric computation",
        "useful as an external benchmark vocabulary; its metrics are not the Kaggle adjusted-edge/division score",
    ),
    "CellTrackingChallenge/2021-edition-available-colabs": method(
        "reusability collection", "method-specific", "five contestant notebooks: CALT-US, nnU-Net, Deepwater, U-SE-ResNet, XB-Net", "method-specific/partly external repositories", "method-specific", "method-specific",
        "all 44 code cells across five notebooks traversed; training and inference recipes preserved", "Colab training/inference recipes", "CTC evaluation recipes in several notebooks", "CTC datasets/Drive paths", "CTC outputs", "method-specific",
        "complete small repository read; it is a reproducibility index rather than one unified algorithm",
    ),
    "WenChentao/3DeeCellTracker": method(
        "3D time-lapse tracker", "cell centers derived from segmentation", "3D U-Net or StarDist wrapper plus watershed utilities",
        "FFN-based local matching followed by PR-GLS nonrigid registration across frames", "lineage handling is not a central explicit branch optimizer in selected implementation", "iterative local matching/registration rather than global lineage ILP",
        "model training APIs exist", "Tracker/TrackerLite pipelines", "internal tracking accuracy utilities; no Biohub metric", "TIFF/NumPy preprocessing", "N/A", "watershed and label correction",
        "relevant 3D motion/registration prior; adaptation to sparse Biohub point labels and divisions would be needed",
    ),
    "quantumjot/btrack": method(
        "Bayesian multi-object tracker", "consumes detections", "N/A", "Bayesian belief matrix with motion/appearance and predicted state uncertainty builds tracklets",
        "branch/divide hypotheses are explicit fates", "multiple-hypothesis global mixed-integer optimization via GLPK", "probabilistic model configuration rather than detector training", "C++ tracker with Python API",
        "no native Biohub metric", "object import/export APIs", "generic exports; no native Kaggle CSV", "global hypothesis selection repairs tracklets",
        "mature lineage optimizer candidate, but detector, coordinate bridge, and competition scoring must be supplied",
    ),
    "raphaelreme/byotrack": method(
        "modular tracking framework", "detector interface", "segmentation/detection supplied by modular front end", "greedy LAP, Kalman linker, and Trackastra wrapper",
        "depends on selected linker/refiner", "framewise assignment; wrapped Trackastra can use its solver", "component-specific", "Detector -> Linker -> Refiner API and CTC example", "CTC metric wrapper", "CTC dataset + GEFF I/O", "N/A native Kaggle CSV", "distance-based stitching and other refiners",
        "useful integration layer to compare linkers under one API; not a ready Biohub submission",
    ),
    "matt-ceran/biohub-cell-tracking": method(
        "competition participant pipeline", "3D DoG adaptive proposals; small 3D CNN appearance filter", "N/A: point centers", "whole-movie min-cost-flow linking",
        "geometric and learned division modules exist, but README says geometric repair is disabled and no development winner frozen", "min-cost flow", "positive-unlabeled appearance training and separate division-head training", "baseline runner",
        "local competition metric implementation; numeric README results remain AUTHOR_CLAIM", "competition arrays/GEFF", "validated submission.csv assembly", "minimum-track-length pruning; division experiments",
        "highly relevant complete participant system; no license file observed, so code reuse is legally constrained",
    ),
    "tarunn613/biohub-cell-tracking": method(
        "competition participant pipeline", "Cellpose-SAM-derived detections", "Cellpose masks converted to centers", "LAP baseline and Motile global tracking",
        "Motile graph allows lineage constraints and pruning", "Motile/ILP-style global solve plus LAP alternative", "pretrained Cellpose; no verified end-to-end training evidence in this read", "baseline CLI", "competition score script; reported numbers are AUTHOR_CLAIM", "OME-Zarr/GEFF paths", "submission assembler", "track pruning",
        "direct competition alternative combining foundation segmentation and global tracking; no license file observed",
    ),
    "phucthaiv02/biohub-cell-tracking": method(
        "competition baseline derivative", "TemporalUNet3D center heatmap", "N/A: point centers", "same SimpleNodeTransformer bytes as official baseline at compared commit",
        "official-style division metric", "baseline greedy/ILP path", "official-style training scripts", "official-style prediction script", "official-style metrics docs/code", "GEFF/tracksdata", "visualization and evaluation path; no csv converter in tree", "anisotropic first pooling stage differs from official baseline",
        "source comparison shows a renamed/modified derivative: node transformer identical, temporal U-Net changed for anisotropic pooling",
    ),
    "sota1111/biohub-claude": method(
        "competition experiment system", "multiscale DoG/peak and learned detector modules", "N/A: point centers", "cross-attention edge model and global min-cost-flow linking",
        "division overlay creates candidate forks", "min-cost flow", "learned detection/edge experiments", "submission builder and experiment CLI", "official/local score implementations", "competition I/O", "submission.csv builder", "division overlay and pruning experiments",
        "broad experiment repository sampled at target-file level only; NOTICE is not a classified open-source license",
    ),
    "tossowski/BioHub": method(
        "competition participant pipeline", "3D learned heatmap detector", "N/A: point centers", "LAP linker or Ultrack-based linker",
        "post-processing/graph logic includes division handling", "Hungarian/LAP or Ultrack optimization", "detection training script", "prediction pipeline", "competition metric implementation", "OME-Zarr/GEFF", "submission builder", "link pruning/repair",
        "complete competition-oriented alternative with both lightweight assignment and Ultrack backend",
    ),
    "m9h/biohub-starter": method(
        "competition validation/research starter", "delegates to official baseline", "N/A", "compares official greedy with ILP and post-processing", "candidate analysis and gradient-boosted division classifier experiments",
        "official ILP plus experiment scripts", "mostly analysis; classifier script trains HistGradientBoostingClassifier", "embryo-disjoint validation workflow", "local competition metric scripts", "GEFF/official baseline outputs", "delegates submission packaging", "short-component filtering, motion relinking, geometric division recovery",
        "main contribution is split/evaluation design; README scores and leaderboard statements are AUTHOR_CLAIM, not independently rerun",
    ),
    "elephant-track/elephant-server": method(
        "interactive deep-learning tracker", "3D U-Net-like detection/segmentation models", "voxel segmentation", "learned flow fields connect frames",
        "temporal affinity/flow design supports lineage reconstruction but no Biohub-specific division scorer observed", "model-based flow rather than selected global ILP", "incremental/interactive train script and losses", "server inference script", "evaluation script", "custom dataset generator", "N/A", "flow/segmentation decoding",
        "scientifically relevant to learned temporal fields; target-file read only, not a ready competition adapter",
    ),
    "MouseLand/cellpose": method(
        "segmentation component", "cell probability and vector-flow prediction", "Cellpose instance segmentation; 3D inference documented", "N/A native lineage tracker", "N/A", "N/A lineage optimization", "segmentation training APIs", "2D/3D segmentation inference", "mask/flow segmentation metrics", "image/mask I/O", "N/A", "flow integration, mask construction/cleanup",
        "powerful front-end candidate only; tracking, divisions, GEFF and Biohub submission remain external",
    ),
    "live-image-tracking-tools/geff-java": method(
        "cross-language GEFF implementation", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "Java read/write/roundtrip API", "cross-language round-trip tests", "Zarr v2 GEFF Java structures and variable-length properties", "N/A", "validation/round-trip only",
        "complete relevant-source read confirms interoperability role, not a tracking method",
    ),
}


CLAIMS = [
    ("GH-CL-001", "royerlab/kaggle-cell-tracking-competition 是本次合同的强制起点，并含训练、推理、指标、GEFF/CSV 转换与测试源码。", "SOURCE_CODE_VERIFIED", "GH-DEEP-royerlab__kaggle-cell-tracking-competition", "direct"),
    ("GH-CL-002", "官方基线用 TemporalUNet3D 产生中心概率，并以 SimpleNodeTransformer 对相邻帧候选节点打分。", "SOURCE_CODE_VERIFIED", "GH-DEEP-royerlab__kaggle-cell-tracking-competition", "direct"),
    ("GH-CL-003", "官方训练损失只在有稀疏标注约束的活动行列上计算边 BCE，未标注区域不是负例。", "SOURCE_CODE_VERIFIED", "GH-DEEP-royerlab__kaggle-cell-tracking-competition", "direct"),
    ("GH-CL-004", "官方评价先做物理距离节点匹配；边与 division 评价均显式处理稀疏标注，division 还用最大基数二分配对避免一次预测分叉重复计分。", "SOURCE_CODE_VERIFIED", "GH-DEEP-royerlab__kaggle-cell-tracking-competition", "direct"),
    ("GH-CL-005", "tracksdata 提供 GEFF 图结构、KDTree 候选边、贪心与 ILP 求解器，但不是检测器。", "SOURCE_CODE_VERIFIED", "GH-DEEP-royerlab__tracksdata", "direct"),
    ("GH-CL-006", "GEFF Python 与 Java 仓库的职责是 Zarr 图交换、schema、验证与跨语言 round-trip，而非学习或执行跟踪。", "SOURCE_CODE_VERIFIED", "GH-DEEP-live-image-tracking-tools__geff;GH-DEEP-live-image-tracking-tools__geff-java", "direct"),
    ("GH-CL-007", "Ultrack 从分割候选、时序边和重叠约束构建 MIP；可用 Gurobi，并在不可用时回退 CBC。", "SOURCE_CODE_VERIFIED", "GH-DEEP-royerlab__ultrack", "direct"),
    ("GH-CL-008", "Trackastra 消费图像与实例 mask，以 transformer 预测对象关联，并提供 greedy_nodiv、greedy 和 ILP 三种图求解模式。", "SOURCE_CODE_VERIFIED", "GH-DEEP-weigertlab__trackastra", "direct"),
    ("GH-CL-009", "py-ctcmetrics 实现 DET/SEG/TRA/LNK/HOTA/CHOTA 等 CTC 指标；这些不能直接替代 Biohub 的 adjusted-edge/division 评分。", "INFERENCE", "GH-DEEP-CellTrackingChallenge__py-ctcmetrics;GH-DEEP-royerlab__kaggle-cell-tracking-competition", "inference"),
    ("GH-CL-010", "3DeeCellTracker、btrack、ByoTrack、ELEPHANT 与 Cellpose 分别提供 3D 配准跟踪、贝叶斯/全局假设、模块化链接、学习流场和分割能力，但均需不同程度的 Biohub 接口适配。", "INFERENCE", "GH-DEEP-WenChentao__3DeeCellTracker;GH-DEEP-quantumjot__btrack;GH-DEEP-raphaelreme__byotrack;GH-DEEP-elephant-track__elephant-server;GH-DEEP-MouseLand__cellpose", "inference"),
    ("GH-CL-011", "phucthaiv02 仓库是官方基线的修改衍生：比较的 SimpleNodeTransformer 字节相同，而 TemporalUNet3D 增加了先 XY 后各向同性的池化。", "SOURCE_CODE_VERIFIED", "GH-DEEP-royerlab__kaggle-cell-tracking-competition;GH-DEEP-phucthaiv02__biohub-cell-tracking", "direct"),
    ("GH-CL-012", "公开参赛仓库展示了多条不同路线：DoG+CNN+min-cost-flow、Cellpose+Motile、热图+LAP/Ultrack、交叉注意力+min-cost-flow。", "INFERENCE", "GH-DEEP-matt-ceran__biohub-cell-tracking;GH-DEEP-tarunn613__biohub-cell-tracking;GH-DEEP-tossowski__BioHub;GH-DEEP-sota1111__biohub-claude", "inference"),
    ("GH-CL-013", "matt-ceran、tarunn613 与 m9h 的固定 tree 未见许可证文件；sota1111 仅见 NOTICE，不能据此推定可再分发完整源码。", "SOURCE_CODE_VERIFIED", "GH-DEEP-matt-ceran__biohub-cell-tracking;GH-DEEP-tarunn613__biohub-cell-tracking;GH-DEEP-m9h__biohub-starter;GH-DEEP-sota1111__biohub-claude", "direct"),
    ("GH-CL-014", "精确比赛仓库搜索报告 37 项、广义短语搜索报告 68 项、Kaggle 变体报告 28 项，并已读取这些集合的全部报告页。", "MEASURED", "GH-SEARCH-EXACT-P1;GH-SEARCH-BROAD-P1;GH-SEARCH-KAGGLE-P1", "direct"),
    ("GH-CL-015", "Code Search 的大结果集仅读取首屏，因此不能声称穷尽 GitHub 全部代码命中。", "MEASURED", "GH-CS-001;GH-CS-002;GH-CS-003;GH-CS-004;GH-CS-005;GH-CS-006;GH-CS-007;GH-CS-008;GH-CS-009", "direct"),
]


def load_deep() -> list[dict]:
    records = []
    for path in sorted(EVIDENCE.glob("*/repo_evidence.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def refresh_deep_collection_summary(deep: list[dict]) -> None:
    """Regenerate the collector roll-up from the current per-repository evidence.

    This avoids retaining stale counts after an interrupted targeted retry updates
    an individual ``repo_evidence.json`` file.
    """
    summaries = []
    for item in deep:
        summaries.append({
            "repo": item["repo"],
            "status": item["read_status"],
            "commit": item["fixed_commit_sha"],
            "branch": item["fixed_branch"],
            "file_count": item["tree_file_count"],
            "read_count": item["files_actually_read_count"],
            "missing_count": len(item.get("target_paths_missing", [])),
            "error_count": len(item.get("read_errors", [])),
            "license": item["license"],
            "evidence": f"evidence/{item['repo'].replace('/', '__')}/repo_evidence.json",
        })
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_count": len(deep),
        "summaries": summaries,
    }
    (ROOT / "deep_read_collection_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def query_url(query: str, search_type: str, page_number: int = 1) -> str:
    return f"https://github.com/search?q={quote_plus(query)}&type={search_type}&p={page_number}"


def build_query_evidence() -> dict:
    pages = []
    for record in REPO_SEARCH_PAGES:
        query = QUERY_DEFS[record["query_id"]][0]
        pages.append({
            **record,
            "search_type": "repository_search",
            "query": query,
            "url": query_url(query, "repositories", record["page"]),
            "access_time_utc": ACCESS_WINDOW,
            "read_scope": "visible main text and repository result links",
        })
    for query_id, query, byte_count, digest in ZERO_REPO_SEARCHES:
        pages.append({
            "source_id": f"GH-SEARCH-{query_id}", "query_id": query_id, "page": 1,
            "reported_total": 0, "bytes": byte_count, "sha256": digest, "repos": [],
            "search_type": "repository_search", "query": query,
            "url": query_url(query, "repositories"), "access_time_utc": ACCESS_WINDOW,
            "read_scope": "visible main text; zero repository results",
        })
    for query_id, query, total, observed, byte_count, digest in CODE_SEARCHES:
        pages.append({
            "source_id": query_id, "query_id": query_id, "page": 1,
            "reported_total": total, "bytes": byte_count, "sha256": digest,
            "unique_file_hits_observed": observed, "search_type": "code_search",
            "query": query, "url": query_url(query, "code"),
            "access_time_utc": ACCESS_WINDOW,
            "read_scope": "first result page only; unique blob paths deduplicated",
        })
    payload = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "access_window_utc": ACCESS_WINDOW,
        "note": "Hashes cover GitHub search page visible main text at read time; timing text can make page hashes dynamic.",
        "pages": pages,
        "ordinary_web_queries": [
            {"query_id": qid, "query": query, "observed_repositories": result.split(";"), "access_time_utc": "2026-09-03T07:30:00Z..2026-09-03T08:05:00Z"}
            for qid, query, result in WEB_QUERIES
        ],
    }
    path = EVIDENCE / "search_query_pages.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_inventory(deep: list[dict], search_payload: dict) -> list[dict]:
    discovered: dict[str, set[str]] = defaultdict(set)
    for item in search_payload["pages"]:
        for repo in item.get("repos", []):
            discovered[repo].add(item["query_id"])
    for repo in CODE_REPOS:
        discovered[repo].add("GH-CODE-FIRST-PAGE-RELEVANT")
    for qid, _, result in WEB_QUERIES:
        for repo in result.split(";"):
            discovered[repo].add(qid)
    deep_by_repo = {item["repo"]: item for item in deep}
    for repo in deep_by_repo:
        discovered[repo].add("GH-DEEP-SELECTION")

    rows = []
    for repo in sorted(discovered, key=str.lower):
        item = deep_by_repo.get(repo)
        if item:
            read_files = item["files_actually_read"]
            relation = item["relation_to_competition"]
            evidence_path = repo_rel(next(EVIDENCE.glob(f"{repo.replace('/', '__')}/repo_evidence.json")))
            stars, forks = STARS.get(repo, (None, None))
            row = {
                "source_id": item["source_id"],
                "owner_repo": repo,
                "url": item["url"],
                "description": METHODS[repo]["role"],
                "relation_to_competition": relation,
                "stars": stars,
                "forks": forks,
                "default_branch": item["fixed_branch"],
                "latest_commit_sha": item["fixed_commit_sha"],
                "latest_commit_date": item["latest_commit_date"],
                "license": item["license"],
                "archived": False,
                "file_count": item["tree_file_count"],
                "read_status": item["read_status"],
                "files_actually_read": ";".join(entry["path"] for entry in read_files),
                "evidence_path": evidence_path,
                "notes": f"queries={';'.join(sorted(discovered[repo]))}; {METHODS[repo]['key_finding']}; GitHub owner/repo identifier is stored in owner_repo.",
            }
        else:
            is_collision = repo.lower().startswith("tracksdata/")
            relation = "NAME_COLLISION_FALSE_POSITIVE" if is_collision else "SEARCH_DISCOVERY_NOT_DEEP_READ"
            row = {
                "source_id": f"GH-DISCOVERY-{repo.replace('/', '__')}",
                "owner_repo": repo, "url": f"https://github.com/{repo}",
                "description": "Search-result repository title/link only",
                "relation_to_competition": relation,
                "stars": "", "forks": "", "default_branch": "",
                "latest_commit_sha": "", "latest_commit_date": "", "license": "NOT_CHECKED",
                "archived": "NOT_CHECKED", "file_count": "",
                "read_status": "TITLE_SNIPPET_ONLY", "files_actually_read": "",
                "evidence_path": repo_rel("evidence/search_query_pages.json"),
                "notes": f"queries={';'.join(sorted(discovered[repo]))}; no README/source claim; GitHub owner/repo identifier is stored in owner_repo.",
            }
        rows.append(row)

    fieldnames = list(rows[0])
    with (ROOT / "github_repository_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def build_query_log(search_payload: dict, deep: list[dict]) -> list[dict]:
    """Write the repository/code query fragment in the canonical query schema."""
    rows = []
    deep_repos = {item["repo"] for item in deep}
    for item in search_payload["pages"]:
        if item["search_type"] == "repository_search":
            returned = len(item.get("repos", []))
            unique_after_dedupe = len(set(item.get("repos", [])))
            deep_read_count = len(set(item.get("repos", [])) & deep_repos)
            category = "github_repository"
            platform = "GitHub Repository Search"
            status = "OK"
            if item["query_id"] == "GH-RS-013":
                status = "PARTIAL"
            notes = (
                f"source_id={item['source_id']}; url={item['url']}; "
                f"response_bytes={item['bytes']}; response_sha256={item['sha256']}; "
                f"access_window_utc={item['access_time_utc']}; scope={item['read_scope']}"
            )
            if item["query_id"] == "GH-RS-013":
                notes += "; page 1 only and name-collision dominated"
        else:
            returned = item.get("unique_file_hits_observed", 0)
            unique_after_dedupe = returned
            deep_read_count = 0
            category = "github_code"
            platform = "GitHub Code Search"
            status = "PARTIAL"
            notes = (
                f"source_id={item['source_id']}; url={item['url']}; "
                f"response_bytes={item['bytes']}; response_sha256={item['sha256']}; "
                "first result page only; per-query blob paths were deduplicated; "
                "deep_read_count=0 because fixed-repository reads were not attributed to an individual code query"
            )
        rows.append({
            "query_id": item["source_id"], "category": category, "platform": platform,
            "query": item["query"], "sort_order": "Best match", "result_page": item["page"],
            "reported_total": item["reported_total"], "actually_obtained": returned,
            "unique_after_dedupe": unique_after_dedupe, "deep_read_count": deep_read_count,
            "access_time_utc": item["access_time_utc"].split("..")[-1],
            "access_time_singapore": singapore_time(item["access_time_utc"].split("..")[-1]),
            "status": status, "evidence_path": repo_rel("evidence/search_query_pages.json"),
            "notes": notes,
        })
    web_window = "2026-09-03T07:30:00Z..2026-09-03T08:05:00Z"
    for query_id, query, result in WEB_QUERIES:
        observed_repos = result.split(";")
        rows.append({
            "query_id": query_id, "category": "github_repository", "platform": "Ordinary web search",
            "query": query, "sort_order": "provider relevance", "result_page": 1,
            "reported_total": "NOT_EXPOSED", "actually_obtained": len(observed_repos),
            "unique_after_dedupe": len(set(observed_repos)),
            "deep_read_count": len(set(observed_repos) & deep_repos),
            "access_time_utc": web_window.split("..")[-1],
            "access_time_singapore": singapore_time(web_window.split("..")[-1]),
            "status": "PARTIAL", "evidence_path": repo_rel("evidence/search_query_pages.json"),
            "notes": f"access_window_utc={web_window}; primary GitHub repository results recorded; ordinary web query was not exhaustive.",
        })
    fieldnames = list(rows[0])
    with (ROOT / "search_query_log.github.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def build_method_matrix(deep: list[dict]) -> None:
    deep_by_repo = {item["repo"]: item for item in deep}
    rows = []
    for repo, values in METHODS.items():
        item = deep_by_repo[repo]
        dependency_files = [entry["path"] for entry in item["files_actually_read"] if entry["category"] == "dependency"]
        files_read = ";".join(entry["path"] for entry in item["files_actually_read"])
        evidence_path = repo_rel(f"evidence/{repo.replace('/', '__')}/repo_evidence.json")
        rows.append({
            "source_id": item["source_id"],
            "owner_repo": repo,
            "commit_sha": item["fixed_commit_sha"],
            "detection": values["detection"],
            "segmentation": values["segmentation"],
            "tracking": values["temporal_linking"],
            "division": values["division_handling"],
            "optimization": values["optimization"],
            "data_loading": values["data_io"],
            "evaluation": values["evaluation"],
            "submission_conversion": values["submission"],
            "dependencies": ";".join(dependency_files) if dependency_files else "N/A_NO_DEDICATED_DEPENDENCY_FILE_OBSERVED",
            "license": item["license"],
            "files_read": files_read,
            "transfer_notes": (
                f"read_status={item['read_status']}; branch={item['fixed_branch']}; "
                f"training={values['training']}; inference={values['inference']}; postprocessing={values['postprocessing']}; "
                f"{values['key_finding']}; evidence_source_ids={item['source_id']}; "
                f"evidence_path={evidence_path}; "
                "schema mapping: temporal_linking->tracking; division_handling->division; original owner/repo->owner_repo"
            ),
        })
    with (ROOT / "github_code_method_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_source_manifest(deep: list[dict], search_payload: dict) -> int:
    records = []
    query_evidence_path = EVIDENCE / "search_query_pages.json"
    query_evidence_digest = hashlib.sha256(query_evidence_path.read_bytes()).hexdigest()
    for item in search_payload["pages"]:
        records.append({
            "source_id": item["source_id"], "source_type": item["search_type"], "platform": "GitHub web",
            "title": f"GitHub {item['search_type']} query page {item['page']}", "author": "GitHub search",
            "url": item["url"], "query": item["query"], "sort_order": "Best match",
            "result_page": item["page"], "result_rank": "page-level",
            "access_time_utc": item["access_time_utc"].split("..")[-1],
            "access_time_singapore": singapore_time(item["access_time_utc"].split("..")[-1]),
            "read_status": "METADATA_ONLY", "bytes_observed": item["bytes"], "sha256": item["sha256"],
            "version_id": "", "commit_sha": "", "license": "GitHub page-specific terms",
            "evidence_path": repo_rel("evidence/search_query_pages.json"), "factual_use_allowed": True,
            "notes": f"Visible main text hash; evidence_file_sha256={query_evidence_digest}; access_window_utc={item['access_time_utc']}; scope={item['read_scope']}",
        })
    for rank, item in enumerate(deep, 1):
        slug = item["repo"].replace("/", "__")
        evidence_path = EVIDENCE / slug / "repo_evidence.json"
        rel_evidence = repo_rel(evidence_path)
        content_index = json.dumps(
            [{"path": entry["path"], "sha256": entry["sha256"]} for entry in item["files_actually_read"]],
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        records.append({
            "source_id": item["source_id"], "source_type": "github_repository_fixed_commit",
            "platform": "GitHub", "title": item["repo"], "author": item["repo"].split("/", 1)[0],
            "url": f"{item['url']}/tree/{item['fixed_commit_sha']}", "query": "deep-read selection",
            "sort_order": "relevance", "result_page": "N/A", "result_rank": rank,
            "access_time_utc": item["access_time_utc"], "access_time_singapore": singapore_time(item["access_time_utc"]),
            "read_status": item["read_status"],
            "bytes_observed": sum(entry["bytes"] for entry in item["files_actually_read"]),
            "sha256": hashlib.sha256(content_index).hexdigest(), "version_id": "",
            "commit_sha": item["fixed_commit_sha"], "license": item["license"],
            "evidence_path": rel_evidence, "factual_use_allowed": True,
            "notes": f"files_read={item['files_actually_read_count']}; tree_files={item['tree_file_count']}; tree_sha256={item['tree_sha256']}; combined hash covers ordered path+file-sha index",
        })
    with (ROOT / "source_manifest.github.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return len(records)


def build_claims(deep: list[dict]) -> None:
    evidence_paths = {item["source_id"]: repo_rel(f"evidence/{item['repo'].replace('/', '__')}/repo_evidence.json") for item in deep}
    rows = []
    for claim_id, text, claim_type, source_ids, directness in CLAIMS:
        paths = []
        for source_id in source_ids.split(";"):
            if source_id in evidence_paths:
                paths.append(evidence_paths[source_id])
            elif source_id.startswith("GH-"):
                paths.append(repo_rel("evidence/search_query_pages.json"))
        rows.append({
            "claim_id": claim_id, "report_section": "GitHub ecosystem", "claim_text": text, "claim_type": claim_type,
            "source_ids": source_ids, "evidence_paths": ";".join(dict.fromkeys(paths)),
            "direct_or_inference": directness,
            "confidence": "HIGH" if directness == "direct" else "MEDIUM",
            "conflict_present": False,
            "conflict_notes": "No direct source conflict observed; model performance and README scores were not independently rerun.",
        })
    with (ROOT / "claims_evidence_matrix.github.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_deep_report(deep: list[dict], inventory: list[dict], manifest_count: int) -> None:
    full_count = sum(item["read_status"] == "FULL_RELEVANT_REPO_SOURCE_READ" for item in deep)
    target_count = len(deep) - full_count
    file_count = sum(len(item["files_actually_read"]) for item in deep)
    lines = [
        "# GitHub 生态固定提交深读草稿",
        "",
        "> 这是 `github_ecosystem` 隔离 staging 草稿，未修改 canonical、未提交、未推送，也未修改任何外部仓库。",
        "",
        "## 结论与证据边界",
        "",
        f"- 发现清单：{len(inventory)} 个去重仓库；其中 19 个固定 branch + 40 位 commit 深读。",
        f"- 深读状态：`FULL_RELEVANT_REPO_SOURCE_READ` {full_count} 个，`TARGET_FILES_READ` {target_count} 个；完整读取并哈希 {file_count} 个文件。",
        f"- source manifest 共 {manifest_count} 条：搜索页与固定 tree 的聚合记录；逐文件 full-bytes 读取清单、bytes 与 SHA-256 保存在各仓库 `repo_evidence.json`。",
        "- `FULL_RELEVANT_REPO_SOURCE_READ` 的含义严格限定为：对固定 commit 的完整 tree 按冻结规则选择全部人类可读代码、Notebook、文档、依赖/运行配置、schema、测试和许可文本，逐文件完整读取；只排除托管自动化、生成/缓存目录及二进制/非源码产物。tree 与逐路径排除原因均保留。它不代表运行过代码、训练过模型或验证过 README 分数。",
        "- `TARGET_FILES_READ` 表示只读取预先选定的相关文件；不能外推为仓库完整源码阅读。`README_ONLY` 本批为 0；未深读仓库统一为 `SEARCH_RESULT_METADATA_ONLY`。",
        "- 所有 README、实验报告和 leaderboard 数字均按 `AUTHOR_CLAIM` 处理；本任务没有执行训练、推理、Kaggle submission 或动态分数回收。",
        "",
        "## 搜索覆盖",
        "",
        "Repository Search 的核心 37、68、28 个比赛相关结果集，以及 Ultrack 21、Trackastra 12、CTC 33、Zebrahub 8、royerlab tracking 5、GEFF 4 等集合均读取全部报告页。`tracksdata in:name` 报告 144 项，但除首项外被同名账号工程结果主导，仅保存首屏并标 `PARTIAL`。九个 Code Search 查询均读取首屏并记录可见文本 bytes/SHA-256 与唯一 blob 数；未继续翻完大结果集，所以不声称穷尽 GitHub Code Search。普通网页搜索保存查询和主要 GitHub 命中，不声称全网穷尽。",
        "",
        "## 关键技术综合",
        "",
        "1. 最接近端到端可复用链条的是官方基线：3D+时间 U-Net 中心检测、节点对 transformer、greedy/ILP 图求解、稀疏标注指标和 GEFF/CSV 转换均在同一固定提交可定位。",
        "2. 生态组件职责要分开：GEFF 是图交换格式；tracksdata 是图模型/求解/评价基础库；Ultrack 是分割候选与跟踪联合优化器；Trackastra 是消费实例 mask 的学习关联器。文件存在不等于接口已接通。",
        "3. 可组合路线包括 Cellpose/3Dee/ELEPHANT 的检测或分割前端、Trackastra/btrack/ByoTrack/Ultrack 的关联与全局约束，以及 CTC 工具的外部评价。但 Biohub 的稀疏点标注、物理坐标、division 计分和 submission.csv 仍需明确适配。",
        "4. 参赛者公开仓库提供 DoG+CNN+min-cost-flow、Cellpose+Motile、热图+LAP/Ultrack、交叉注意力+min-cost-flow 等备选。其 README 分数未独立复跑；无许可证仓库仅可作为研究线索，不应复制完整源码。",
        "",
        "## 逐仓库深读记录",
        "",
    ]
    for index, item in enumerate(deep, 1):
        repo = item["repo"]
        values = METHODS[repo]
        evidence_path = repo_rel(f"evidence/{repo.replace('/', '__')}/repo_evidence.json")
        tree_path = repo_rel(f"evidence/{repo.replace('/', '__')}/tree.txt")
        sha = item["fixed_commit_sha"]
        if len(sha) != 40:
            raise ValueError(f"non-40-char commit for {repo}: {sha}")
        lines.extend([
            f"### {index}. `{repo}`",
            "",
            f"- 固定提交：branch `{item['fixed_branch']}`，commit `{sha}`，commit date `{item['latest_commit_date']}`。",
            f"- 阅读状态：`{item['read_status']}`；完整 tree {item['tree_file_count']} 个 blob；实际读取文件 {item['files_actually_read_count']} 个；missing {len(item['target_paths_missing'])}；read error {len(item['read_errors'])}。",
            f"- 许可证观察：`{item['license']}`。无许可或只有 NOTICE 时，不推定再分发权。",
            f"- 证据路径：`{evidence_path}`；tree：`{tree_path}`。",
            f"- 角色：{values['role']}。",
            f"- 方法：检测={values['detection']}；分割={values['segmentation']}；时序链接={values['temporal_linking']}；division={values['division_handling']}；优化={values['optimization']}。",
            f"- 训练/推理/评价：训练={values['training']}；推理={values['inference']}；评价={values['evaluation']}。",
            f"- I/O 与后处理：I/O={values['data_io']}；submission={values['submission']}；后处理={values['postprocessing']}。",
            f"- 判定：{values['key_finding']}",
            "- 类别覆盖：" + "；".join(
                f"{category}={meta['status']}" for category, meta in item.get("category_coverage", {}).items()
            ) + "。",
            "- 实际读取文件：",
            "",
        ])
        for entry in item["files_actually_read"]:
            notebook_note = ""
            if "notebook" in entry:
                nb = entry["notebook"]
                notebook_note = f"；Notebook cells={nb['cell_count']}, code={nb['code_cell_count']}, markdown={nb['markdown_cell_count']}, all_code_cells_traversed={nb['all_code_cells_traversed']}"
            lines.append(f"  - `{entry['path']}` — category `{entry['category']}`；{entry['bytes']} bytes；SHA-256 `{entry['sha256']}`{notebook_note}")
        lines.append("")
    lines.extend([
        "## 组合建议（推断，不是已验证性能结论）",
        "",
        "- 最小风险基线：保留官方数据/指标/submission 合同，只在 detector、edge scorer 或 solver 单点替换；每次用同一稀疏标注 evaluator 比较。",
        "- 分割前端试验：Cellpose、3Dee 或 Ultrack segmentation 可产生实例/候选，但必须先定义 mask/center 到物理 `(z,y,x)` 与 GEFF node 的确定性转换。",
        "- 关联后端试验：Trackastra 适合从实例 mask 学习关联；btrack 适合概率 tracklet + division hypothesis；Ultrack 适合将层级分割候选与全局流约束联合求解。三者不能仅凭 README 断言优于官方。",
        "- 数据交换：以 GEFF/tracksdata 作为图中间层有利于组件解耦；必须保留 directed axes、node/edge property schema、solution edge 和坐标单位。",
        "",
        "## 未解决与阻断",
        "",
        "- 本子任务早期在默认隔离上下文调用 `gh auth status` / `gh api` 时得到 `LOGIN_REQUIRED`；这只是该隔离调用的访问失败，不能外推为主环境当前凭据无效。根任务随后已在获批环境独立验证 `gh api user` 为 SailorRen 且可用，二者按执行上下文并存记录。匿名 REST 调用另触发出口 IP rate limit。深读使用只读 Git 协议固定 SHA，搜索使用已登录的应用内 GitHub 页面。",
        "- Code Search 与 `tracksdata in:name` 未全分页，故本报告是冻结查询集内的系统性侦察，不是 GitHub 全宇宙穷举。",
        "- 未运行任何第三方仓库，依赖可安装性、GPU/内存、模型权重可获得性、Kaggle 无网兼容性均 `NOT_RUN`。",
        "- 未读取或复制无许可仓库的完整源码到持久产物；仅保存固定 URL、tree、哈希、结构统计和自写摘要。",
        "",
    ])
    (ROOT / "github_deep_read.md").write_text("\n".join(lines), encoding="utf-8")


def build_failure_log(deep: list[dict]) -> None:
    read_errors = sum(len(item["read_errors"]) for item in deep)
    text = f"""# GitHub 访问失败与覆盖限制

## 已观察失败

- `LOGIN_REQUIRED` — 仅本子任务早期默认隔离上下文中的 `gh auth status` / `gh api` 调用返回凭据不可用。它不是主环境当前认证状态：根任务后来在获批环境独立验证 `gh api user` 为 `SailorRen` 且 PASS。没有改 token、没有重新登录。
- `RATE_LIMITED` — 匿名 GitHub REST API 返回 HTTP 403，响应明确为该出口 IP 的 API rate limit exceeded，remaining=0。未把它误写成仓库不存在。
- `BLOCKED` — 默认本地沙箱中的 partial-clone blob 补取首次因 `Could not resolve host: github.com` 失败；随后仅对公开固定提交做获批的只读 blob 读取。没有任何 GitHub 写调用。

## 结果边界

- 深读仓库数：{len(deep)}；最终逐文件读取错误数：{read_errors}。
- GitHub Code Search 九个大查询仅首屏，状态为 `PARTIAL_FIRST_PAGE_ONLY`；不是完整代码索引。
- `tracksdata in:name` 报告 144 项但只读首屏 10 项，其中 9 项为同名账号的明显主题碰撞；状态为 `PARTIAL_PAGE_1_ONLY_NAME_COLLISION_DOMINATED`。
- 普通网页搜索只保留主要 GitHub 结果，未声称全网穷尽。
- 仓库运行、模型下载、训练、推理、Kaggle 提交及动态分数均 `NOT_RUN`。

## 外部副作用核对

- GitHub commit/push/fork/issue/PR/release：0。
- 外部仓库文件修改：0。
- 持久化的第三方完整源码：0；临时 shallow/partial clones 位于 `/tmp`，持久证据仅为 URL、commit、tree、hash、结构统计与自写摘要。
"""
    (ROOT / "access_failures.github.md").write_text(text, encoding="utf-8")


def main() -> None:
    deep = load_deep()
    if len(deep) != 19:
        raise ValueError(f"expected 19 deep repositories, got {len(deep)}")
    refresh_deep_collection_summary(deep)
    search_payload = build_query_evidence()
    inventory = build_inventory(deep, search_payload)
    query_rows = build_query_log(search_payload, deep)
    build_method_matrix(deep)
    manifest_count = build_source_manifest(deep, search_payload)
    build_claims(deep)
    build_deep_report(deep, inventory, manifest_count)
    build_failure_log(deep)
    for source_name, merge_name in {
        "github_repository_inventory.csv": "11_github_repository_inventory.csv",
        "github_deep_read.md": "12_github_deep_read.md",
        "github_code_method_matrix.csv": "13_github_code_method_matrix.csv",
        "source_manifest.github.jsonl": "00_source_manifest.github_fragment.jsonl",
        "claims_evidence_matrix.github.csv": "19_claims_evidence_matrix.github_fragment.csv",
        "access_failures.github.md": "20_access_failures.github_fragment.md",
        "search_query_log.github.csv": "21_search_query_log.github_fragment.csv",
    }.items():
        (ROOT / merge_name).write_bytes((ROOT / source_name).read_bytes())
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "discovered_repository_count": len(inventory),
        "deep_repository_count": len(deep),
        "full_relevant_repository_count": sum(item["read_status"] == "FULL_RELEVANT_REPO_SOURCE_READ" for item in deep),
        "target_files_repository_count": sum(item["read_status"] == "TARGET_FILES_READ" for item in deep),
        "files_fully_read_count": sum(len(item["files_actually_read"]) for item in deep),
        "deep_read_error_count": sum(len(item["read_errors"]) for item in deep),
        "query_log_row_count": len(query_rows),
        "source_manifest_row_count": manifest_count,
    }
    (ROOT / "github_ecosystem_output_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
