# GPT-NL
## Setup
- copy `config.py.example` to `config.py` and fill in your credentials
- `sudo docker compose up -d`

## Run scrapers
- Officiële Bekendmakingen: `sudo docker exec -it gpt-nl-app-1 ./manage.py officiele-bekendmakingen`
- Koninklijke Bibliotheek: `sudo docker exec -it gpt-nl-app-1 ./manage.py kb`
- Planbureau voor de Leefomgeving: `sudo docker exec -it gpt-nl-app-1 ./manage.py pbl`
