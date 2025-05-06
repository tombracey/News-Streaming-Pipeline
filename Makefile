# Install dependencies locally
dependencies:
	pip install -r requirements.txt

# Check PEP-8 compliance of Python code
lint:
	flake8 src/handler.py test/

# Run safety
security-check:
	safety scan --full-report

# Run pytests
tests:
	pytest test/

# Run all deployment steps
deploy: dependencies lint security-check tests