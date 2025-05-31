# fulcrum
An events website for UWCS

Key features include:
- Event creation and management
- Integration with UWCS auth
- iCal generation
- Automated publicity
- Initial email generation
- more soonTM

Note the site uses the same stack (Flask, SQLAlchemy) as [CS139](https://warwick.ac.uk/fac/sci/dcs/teaching/modules/cs139/), to enable easy maintenance and development by most DCS students. As a result, it is reccomended that limited javascript is used. The one exception to this is using bootstap CSS because I'm not a monster.

## Running

```bash
pip install pipenv
pipenv install
pipenv run python build_scss.py
pipenv run flask --app fulcrum run
```

For production, use a gunicorn server:

```bash
...
pipenv run gunicorn fulcrum:app -b 0.0.0.0:5000
```

Alternarively, you can run the site in a docker container:

```bash
docker build -t fulcrum .
docker run -p 5000:5000 fulcrum
```

## Naming

UWCS has a tradition of naming projects by a convoluted scheme. Previous names for websites are: Reinhardt, Zarya, Dextre, and Stardust. The generic theme is rough links. Reinhardt and Zarya are both characters in Overwatch; Zarya and Dextre are both things on the International Space Station; Stardust is the significantly upgraded version of the Dexter malware (we struggled with this). Stardust is also the codename of the Death Star in Star Wars, fulcrum is the codename of Asoka Tano in Star Wars.  

For future projects branching off stardust, I would reccomend Henry Cavill Movies; for this site something physisc-y (Fulcrum is the pivot point of a lever).