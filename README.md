## Description

Telegram bot to connect 'Traininginparks' team members togather and make their sport life easier!

Bot available at [http://t.me/moscowtraining_bot](http://t.me/moscowtraining_bot)

## Functionality

Currently supported functionalities:

- List upcoming train events (get from [Google Calendar](https://calendar.google.com/calendar/embed?src=kaf5qkq0jeas32k56fop5k0ci0%40group.calendar.google.com&ctz=Europe/Moscow))
- Sign up for the train
- List train's attendees

## Deployments

[Heroku](http://heroku.com) app `traininginparks` is set up to autodeploy from `master` branch.

The following env variables are set up to run bot:

- `TOKEN`: Bot token from Telegram @BotFather
- `BOTAN_API_KEY`: API key for [botan](http://appmetrica.yandex.com) stats posting
- `GOOGLE_CREDENTIALS`: Credentials for Google API connection
- `SCOPES`: Scopes to connect thru Google API, only Calendar in `readonly` is set
- `TRAIN_CALENDAR_ID`: Calendar ID in [Google Calendar](https://calendar.google.com) for trains
- `EBENTS_CALENDAR_ID`: Calendar ID in [Google Calendar](https://calendar.google.com) for events
- `MONGODB_URI`: URI with auth to connnect MongoDB
- `LOGDNA_KEY`: Key for LogDNA service
- `MAPS_API`: Google Maps API key
- `YANDEX_PASSWORD`: password for `traininginparks@yandex.ru` account

