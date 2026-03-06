import os

# Folder paths
EXPORTS_TO_ADD_PATH          = "exports_to_add"
EXTRACTED_TEAMS_PATH         = "extracted_teams"
EXTRACTED_REFEREES_PATH      = "extracted_referees"
PATCHES_CONTENTS_PATH        = "patches_contents"
PATCHES_OUTPUT_PATH          = "patches_output"
SIDELOAD_PATH                = "sideload"
ENGINES_PATH                 = "Engines"

# Settings files
SETTINGS_PATH                = "settings.ini"
SETTINGS_ADVANCED_PATH       = os.path.join(ENGINES_PATH, "settings_advanced.ini")

# Team files
TEAMS_LIST_PATH              = "teams_list.txt"
TEAMNOTES_PATH               = "teamnotes.txt"

# Logs
SUGGESTIONS_LOG_PATH         = "suggestions.log"
ISSUES_LOG_PATH              = "issues.log"
CRASH_LOG_PATH               = "crash.log"

# Run batch
RUN_BATCH_PATH               = os.path.join(ENGINES_PATH, "compiler_run.bat")

# State files
STATE_FOLDER_PATH            = os.path.join(ENGINES_PATH, "state")
CHECK_LAST_PATH              = os.path.join(STATE_FOLDER_PATH, "update_check_last.txt")
SKIP_LAST_PATH               = os.path.join(STATE_FOLDER_PATH, "update_skip_last.txt")
ADMIN_WARNED_PATH            = os.path.join(STATE_FOLDER_PATH, "admin_warned.txt")
FIRST_RUN_DONE_PATH          = os.path.join(STATE_FOLDER_PATH, "first_run_done.txt")
DT00_WRITE_ALLOWED_PATH      = os.path.join(STATE_FOLDER_PATH, "dt00_write_allowed.txt")
SIDELOAD_WARNED_PATH         = os.path.join(STATE_FOLDER_PATH, "sideload_warned.txt")
VER_MISMATCH_WARNED_PATH     = os.path.join(STATE_FOLDER_PATH, "ver_mismatch_warned.txt")

# Template files
TEMPLATE_FOLDER_PATH         = os.path.join(ENGINES_PATH, "templates")
DUMMY_MTL_NAME               = "dummy.mtl"
DUMMY_MODEL_NAME             = "oral_dummy_win32.model"
GENERIC_FPKD_NAME            = "generic.fpkd"
KIT_MASK_NAME                = "kit_mask.dds"
FACE_DIFF_BIN_NAME           = "face_diff.bin"

# Refs template paths
REFS_TEMPLATE_PREFOX_PATH    = os.path.join(TEMPLATE_FOLDER_PATH, "refscpk_prefox")
REFS_TEMPLATE_FOX_PATH       = os.path.join(TEMPLATE_FOLDER_PATH, "refscpk_fox")

# Settings tools
SETTINGS_DEFAULT_PATH        = os.path.join(TEMPLATE_FOLDER_PATH, "settings_default.ini")
SETTINGS_TRANSFER_TABLE_PATH = os.path.join(TEMPLATE_FOLDER_PATH, "settings_transfer_table.txt")

# Bin files
BIN_FOLDER_PATH              = os.path.join(ENGINES_PATH, "bins")
TEAMCOLOR_BIN_NAME           = "TeamColor.bin"
UNICOLOR_BIN_NAME            = "UniColor.bin"
UNIPARAM_NAME                = "UniformParameter.bin"
UNIPARAM_18_NAME             = "UniformParameter18.bin"
UNIPARAM_19_NAME             = "UniformParameter19.bin"

# PES-specific paths
UNIFORM_COMMON_PREFOX_PATH   = 'model/character/uniform/common/'
UNIFORM_COMMON_FOX_PATH      = '/Assets/pes16/model/character/common/'

# DirectXTex
TEXCONV_PATH                 = os.path.join(ENGINES_PATH, "directxtex", "texconv.exe")

# Other
MOVED_CPKS_TXT_NAME          = "these_cpks_were_moved_to_download_folder.txt"
