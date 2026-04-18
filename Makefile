.PHONY: init-db dev run build docker-run deploy

init-db:
	python init_db.py

dev:
	python -m flask --app wsgi:app --debug run --host 0.0.0.0 --port 8080

run:
	gunicorn -w 2 -b :8080 wsgi:app

build:
	docker build -t tracking-colis-cloudrun:local .

docker-run:
	docker run --rm -p 8080:8080 --env-file .env tracking-colis-cloudrun:local

deploy:
	gcloud builds submit --config cloudbuild.yaml .
