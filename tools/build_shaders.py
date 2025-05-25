"""Script for building all shaders in the project."""

import os
import subprocess

project_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

for filename in os.listdir(os.path.join(project_dir, "shaders")):
    if filename.endswith(".vert") or filename.endswith(".frag"):
        shader_path = os.path.join(project_dir, "shaders", filename)
        output_path = os.path.join(project_dir, "data", "shaders", filename + ".qsb")
        subprocess.run(
            ["pyside6-qsb", "--qt6", shader_path, "-o", output_path],
            check=True,
        )
