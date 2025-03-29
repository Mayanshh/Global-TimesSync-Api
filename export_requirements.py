import toml
import re

# Load pyproject.toml
with open('pyproject.toml', 'r') as f:
    pyproject = toml.load(f)

# Extract dependencies
dependencies = pyproject['tool']['poetry']['dependencies']

# Convert to requirements.txt format
requirements = []
for package, version in dependencies.items():
    if package == 'python':
        continue
    # Remove ^ from version specifiers
    if isinstance(version, str):
        version = re.sub(r'^\^', '', version)
        requirements.append(f"{package}=={version}")
    else:
        requirements.append(package)

# Write to requirements.txt
with open('requirements.txt.new', 'w') as f:
    f.write('\n'.join(requirements) + '\n')

print("Generated requirements.txt.new")