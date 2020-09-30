printf "\nUpdating setup.py\n"
dephell deps convert --from=pyproject.toml --to=setup.py

printf "\nUpdating requirements.txt\n"
dephell deps convert --from=pyproject.toml --to=requirements.txt

printf "\n"
poetry build

printf "\nNow you may type: poetry publish\n\n"
