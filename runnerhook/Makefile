test:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	. .venv/bin/activate && pip install -r requirements_test.txt
	touch .venv/update_time
	. .venv/bin/activate && python -m pytest -vrf --cov-report term-missing --cov=. --cov-config=.coveragerc --disable-pytest-warnings

lint:
	. .venv/bin/activate && pylint handler.py
