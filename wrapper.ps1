echo ":: Starting wrapper script"

./venv/Scripts/activate

echo ":: Starting collector for EarthPorn"
python shared_code/cli.py run-collector -s EarthPorn