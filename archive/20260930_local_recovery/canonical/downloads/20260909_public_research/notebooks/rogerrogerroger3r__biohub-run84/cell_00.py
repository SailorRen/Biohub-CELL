
import os
BIOHUB_PRESET = 'harmonic_v3_division_wide'
BIOHUB_SCORE_AXIS = 'v19c reported LB 0.939 sister separation radius 14um arm'

os.environ["BIOHUB_OUTPUT_FILTER_SHORT_TRACKS"] = "1"
os.environ["BIOHUB_DET_THRESHOLD"] = "0.965"  # x54: v19 swept DOWN from 0.96875 (0.96->0.937, 0.95->0.937, 0.94->0.936) so their own gradient points UP, and they stopped. Dense LB punishes over-detection; raising the detection threshold is the most direct volume reduction available.
os.environ["BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD"] = "0.25"  # x56: STACK. x40 (0.26) moved divisions 148->87 and scored 0.942; x54 (DET 0.975) moved NODES -1.1% while leaving divisions at 152. Measured orthogonal: different counters, so they should compose.
os.environ["BIOHUB_MOTION_RELINK_LEARNED_BONUS"] = '3.0'  # mianwang1024/biohub-relink-v1 (author LB 0.946): 'relink bonus 3.0 / tight 7.0 / relaxed 11.0 -- local 199-movie CV 0.91944'
os.environ["BIOHUB_MOTION_RELINK_TIGHT_UM"] = '7.0'  # pipeline default 6.0
os.environ["BIOHUB_MOTION_RELINK_RELAXED_UM"] = '11.0'  # pipeline default 10.0
os.environ["BIOHUB_ILP_APPEARANCE_WEIGHT"] = "0.0"
os.environ["BIOHUB_ILP_DISAPPEARANCE_WEIGHT"] = "2"
os.environ["BIOHUB_GAP_CLOSE_MAX_GAP"] = "2"
os.environ["BIOHUB_GAP_CLOSE_UM"] = "5.0"
os.environ["BIOHUB_GAP_DENSITY_ADAPTIVE"] = "1"
os.environ["BIOHUB_GAP_DENSITY_REFERENCE_UM"] = "6.5"
os.environ["BIOHUB_GAP_DENSITY_GAIN"] = "0.040"
os.environ["BIOHUB_GAP_DENSITY_MAX_STEP_DELTA_UM"] = "0.125"
os.environ["BIOHUB_GAP_DENSITY_NEIGHBORS"] = "3"
os.environ["BIOHUB_OUTPUT_MIN_TRACK_LEN"] = "6"
os.environ["BIOHUB_OUTPUT_KEEP_DIVISION_COMPONENTS"] = "1"
os.environ["BIOHUB_OUTPUT_GAP2_RECOVERY"] = "1"
os.environ["BIOHUB_SAFE_DIV_MAX_UM"] = "9.0"  # Max parent-to-daughter separation for an accepted division.
#   Ground-truth parent-daughter links reach 10.4um; a 7um cap rejected ~25% of real links.
#   Loosening 7->9 recovers wide-but-genuine divisions (this is the "sdm9" arm; alone it scored LB 0.939).
os.environ["BIOHUB_SAFE_DIV_SISTER_MAX_UM"] = "14.0"  # Max daughter-to-daughter separation for an accepted division.
#   Ground-truth divisions have sister separations up to 13.7um (median 10.4, p90 13.0), so a 12um cap
#   rejected ~29% of real divisions; 14um admits all of them while the symmetry, mutual-NN, divergence
#   and DeepCenter gates still suppress spurious wide pairs.
os.environ["BIOHUB_SAFE_DIV_SISTER_SYMMETRY_TAU"] = "0.6"  # Sister-symmetry precision gate: reject a proposed division whose two
os.environ["BIOHUB_SAFE_DIV_DIVERGE_UM"] = "2.25"  # Forward-divergence precision gate (default 2.25); larger=stricter, rejects non-separating spurious forks. kimi-v18 LB sweep peaked ~4.0-4.5.
#   daughter distances from the parent differ by more than 60% of their mean (a wildly-asymmetric,
#   almost-always-spurious split). Freeing that slot lets the genuine symmetric division form.
os.environ["BIOHUB_SAFE_DIV_EXISTING_CHILD_MAX_UM"] = "10.0"
os.environ["BIOHUB_SAFE_DIV_FRAME_FRAC_CAP"] = "0.0076"
os.environ["BIOHUB_SAFE_DIV_GLOBAL_FRAC_CAP"] = "0.00375"
# Encourage the ILP to natively predict divisions rather than just disappearing/reappearing
os.environ["BIOHUB_ILP_DIVISION_WEIGHT"] = "1.2"     # Up from 1.0
os.environ["BIOHUB_ADAPTIVE_SHORT_TRACK_RESCUE"] = "1"
os.environ["BIOHUB_SHORT_TRACK_RESCUE_MIN_LEN"] = "4"
os.environ["BIOHUB_SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB"] = "0.88"
os.environ["BIOHUB_SHORT_TRACK_RESCUE_MAX_MEAN_EDGE_DIST_UM"] = "3.0"
os.environ["BIOHUB_SHORT_TRACK_RESCUE_MAX_NODES_FRAC"] = "0.012"
os.environ["BIOHUB_SHORT_TRACK_RESCUE_MAX_NODES_ABS"] = "120"
os.environ["BIOHUB_USE_DEEPCENTER_VETO"] = "1"
os.environ["BIOHUB_REQUIRE_DEEPCENTER_VETO"] = "1"
os.environ["BIOHUB_DEEPCENTER_EXPECTED_EPOCH"] = "2"
os.environ["BIOHUB_DEEPCENTER_GAP_CONFIRM_MIN_SPAN_UM"] = "8.5"
os.environ["BIOHUB_DEEPCENTER_CHECKPOINT"] = "/kaggle/input/biohub-deepcenter-unet3d-center-prior-v1/weights/full_frame_center/best.pt"
os.environ["BIOHUB_DEEPCENTER_GAP_VETO"] = "1"
os.environ["BIOHUB_DEEPCENTER_GAP_THRESHOLD"] = "0.25"
os.environ["BIOHUB_DEEPCENTER_SAFE_DIV_VETO"] = "1"
os.environ["BIOHUB_RUN_OUTPUT_DIAGNOSTICS"] = "0"
os.environ["BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"] = "0.15"
os.environ["BIOHUB_BIDIRECTIONAL_FUSION_MODE"] = "harmonic_probability"
os.environ["BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION"] = "0.90"
os.environ["BIOHUB_DIAGNOSTIC_ARM"] = "harmonic_association_production"

print("BIOHUB_PRESET:", BIOHUB_PRESET)
print("BIOHUB_SCORE_AXIS:", BIOHUB_SCORE_AXIS)