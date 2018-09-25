Scrape the appointment page and send a DM if an appointment is available. Appointment data also go to an sqlite3 db.

Highly unstable, personal use only :).

Sample config:
```
{
    "consumer_key": "lol"
    "consumer_secret": "lol",
    "access_token_key": "lol",
    "access_token_secret": "lol",
    "notify": "your_twitter_handle",
    "db_path": "./lol.db",
    "lock_dir": "/tmp/embassy",
    "categories": [3, 4]
}
```

Categories are based on this:
```
category_map = {
    1: 'Passports',
    2: 'Power of Attorney',
    3: 'Military',
    4: 'Certificates',
    5: 'Permanent Residence',
    6: 'Moving to Greece',
    7: 'Nationality',
    8: 'Notarizations'
}
```

Issue 1: If you message yourself then you don't get notified, I had to create a separate twitter acct just for this thing.

Issue 2: You must follow the twitter acct that sends the DMs otherwise this will not work
