import os
import shutil


def dummy_replace(dummytexture_filename, kittexture_filename, team_id, team_name, main_destination_path):

    kittexture_filepath = os.path.join(main_destination_path, "Kit Textures", kittexture_filename.format(team_id))

    team_commonfolder_path = os.path.join(main_destination_path, "Common", team_id)
    dummytexture_filepath = os.path.join(team_commonfolder_path, dummytexture_filename)

    if not os.path.exists(dummytexture_filepath):
        return

    if os.path.exists(kittexture_filepath):
        os.remove(dummytexture_filepath)
        shutil.copy(kittexture_filepath, team_commonfolder_path)
        os.rename(os.path.join(team_commonfolder_path, kittexture_filename.format(team_id)), dummytexture_filepath)
    else:
        print(f"- Team {team_name} has a {dummytexture_filename} texture in their common folder but their kit 1 does not")
        print(f"- have a corresponding {kittexture_filename} texture. This dummy texture will not be replaced.")


def dummy_kits_replace(team_id, team_name, main_destination_path):

    kittexture_filenames = [
        "u0{}p1.ftex",
        "u0{}p1_back.ftex",
        "u0{}p1_chest.ftex",
        "u0{}p1_leg.ftex",
        "u0{}p1_name.ftex",
        "u0{}p1_nrm.ftex",
        "u0{}p1_srm.ftex"
    ]
    dummytexture_filenames = [
        "dummy_kit.ftex",
        "dummy_kit_back.ftex",
        "dummy_kit_chest.ftex",
        "dummy_kit_leg.ftex",
        "dummy_kit_name.ftex",
        "dummy_kit_nrm.ftex",
        "dummy_kit_srm.ftex"
    ]

    for kittexture_filename, dummytexture_filename in zip(kittexture_filenames, dummytexture_filenames):
        dummy_replace(dummytexture_filename, kittexture_filename, team_id, team_name, main_destination_path)
