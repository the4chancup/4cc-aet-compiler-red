# Prepare a list of dependencies as dictionaries
DEPENDENCIES: list[dict[str, str]] = [
    {
        "name_package": "py7zr",
        "version":      "any",
        "name_pip":     "py7zr",
        "name_user":    "Py7zr (7z extractor)",
    },
    {
        "name_package": "commentedconfigparser",
        "version":      "==3.0.0",
        "name_pip":     "commented-configparser",
        "name_user":    "Commented Config Parser (config file parser)",
    },
    {
        "name_package": "rich",
        "version":      "any",
        "name_pip":     "rich",
        "name_user":    "Rich (rich text console output)",
    },
]
