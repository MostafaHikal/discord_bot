# Discord Gaming Buddy: Build Notes

Private Discord bot for a small server of about 10 people. See
`Full_Development_Plan.md` for scope and behavior. These notes cover what has
been built and the decisions made while building it.

Inspiration: https://github.com/6marwan6/valorant-premier-bot

## Phase 1 — Discord Foundation (2026-10-15) ✅

The plan scope was: Discord application, project structure, environment
settings, request signature verification, interactions endpoint, `/ping`, and
automated tests. All of it was built, but the bot was never connected to
Discord (see "Why Discord is not connected yet").

**Built**

- Discord application created in the Developer Portal, with the bot token,
  application ID, public key and server ID kept in `.env`. The bot is in the
  test server and shows as Offline, because this phase only receives HTTP
  requests from Discord. That stays true until Phase 3.
- `helpers/config.py`: `Settings` declares every variable the app needs, so a
  missing or unknown one fails with a clear error. Routes read it through
  `Depends(get_settings)`.
- `helpers/signature.py`: `is_valid_signature()` confirms a request was really
  signed by Discord, and returns `False` instead of raising on any bad input.
- `POST /api/v1/interactions` (`routes/interactions.py`): checks the signature
  on the raw body and returns `401` if it fails. Only a verified request is
  parsed and passed to `InteractionController`.
- `InteractionController`: answers PING with PONG, answers `/ping` publicly,
  and answers anything else with a private message.

**How a request flows**

Discord posts to `interactions()`, which gets the settings through
`get_settings()` and runs `is_valid_signature()` on the raw body. A bad
signature stops there with `401`. A good one is parsed and handed to
`InteractionController.handle()`, which answers a PING directly and sends
slash commands to `handle_command()`. Every reply is built by `message()`.
The route only knows about HTTP and the controller only knows about Discord
payloads, so a new command later only touches `handle_command()`.

**Why Discord is not connected yet**

Discord can only send requests to a public URL, and the app runs on
`localhost`, so it can't reach it. That left two ways to connect them.

The first was hosting the bot on a server. I didn't want to do that while the
app is still being built: every change would need a redeploy, and an
unfinished app would be running live just so I could test a few lines.

The second was a tunnel, a tool that gives the local app a temporary public
URL. It would have worked, but the URL changes every time the tunnel
restarts, and Discord needs the new URL saved and verified in the Developer
Portal each time. Repeated all day, that gets tiring fast.

So I chose to test locally by imitating Discord. Discord signs every request
with a private key that only Discord has, so the tests generate their own key
pair, sign requests the same way Discord does, and send them straight into
the app. The whole path above runs for real. The only thing missing is the
actual network call from Discord, which waits for deployment.

**Verified**

The tests act as a fake Discord. Each run creates its own throwaway key pair
and signs requests with it, the same way Discord signs its requests, then
gives the app the matching public key instead of the real one. That way no
real `.env` is needed.

The signature check is tested on its own: a correct signature passes, and a
wrong key, a changed body or a bad value fails. The endpoint is tested as a
whole: a correctly signed PING gets a PONG, a request that fails the check
gets `401`, `/ping` replies `Pong`, and an unknown command gets a private
reply.

All tests passed.

**Not verified**

- Discord has never called this endpoint. The tests prove our code is correct,
  not that Discord accepts the URL.
- Deferred to deployment: registering `/ping` with Discord (until then it does
  not appear in the server), a public URL, setting it as the endpoint in the
  Developer Portal, and trying `/ping` live.

## Phase 2 — Member System (2026-10-29) ✅

The plan scope was: users database, automatic member registration, member
settings, and admin permission checks. All four are built. Registration is a
function that nothing calls yet, because it gets connected in Phase 3.

**Built**

- `helpers/database.py`: the database engine, the session maker and
  `get_session()`.
- `helpers/config.py`: two new settings, `DATABASE_URL` and an optional
  `TEST_DATABASE_URL`.
- `scripts/check_db.py`: a script I run by hand to confirm the app can reach
  Neon.
- `models/db_schemes/BaseScheme.py` and `User.py`: the `users` table.
- `helpers/constants.py`: `PROTECTED_TOPICS`, the default topic list.
- `alembic/`: migrations, with the first one creating `users` in Neon.
- `models/BaseDataModel.py` and `UserModel.py`: everything the app can do
  with the `users` table.
- `helpers/permissions.py`: `is_admin()`.

**Connecting to Neon**

SQLAlchemy in async mode with the `asyncpg` driver, since the rest of the app
is async. The URL Neon gives out has to be edited into this form: `+asyncpg`
added after `postgresql`, and only `?ssl=require` kept at the end.

```text
postgresql+asyncpg://USER:PASSWORD@HOST/DBNAME?ssl=require
```

`database.py` has one Engine for the whole app and a Session per piece of
work. Two settings matter:

- `pool_pre_ping=True` checks a pooled connection is still alive before using
  it, because Neon suspends idle databases.
- `expire_on_commit=False` keeps objects readable after saving. Without it,
  async code raises an error when SQLAlchemy tries to reload them.

All commands (scripts, tests, Alembic) are run from inside `src`. Settings
read `.env` from the folder the command runs in, and the imports
(`from models...`) assume `src` is the root.

**The `users` table**

| Column | Type | Notes |
|---|---|---|
| `id` | integer | primary key, our own internal ID |
| `discord_id` | big integer | unique |
| `display_name` | text | |
| `roast_intensity` | integer | default 50 |
| `memory_enabled` | true/false | default true |
| `protected_topics` | JSONB list of text | default topics |
| `first_seen` | timestamp with timezone | |
| `last_seen` | timestamp with timezone | |

Decisions:

- **Internal `id` next to `discord_id`.** The plan identifies a member by
  Discord ID. I added an internal `id` and kept `discord_id` as a unique
  column. Other tables (messages, memories, votes) will point at `users.id`,
  which is also how the plan's own relationship diagram draws it. Using
  `discord_id` as the primary key would have worked too, so this is a design
  choice, not a necessity.
- **`discord_id` is a big integer.** A Discord ID has about 18 digits, which
  doesn't fit a normal integer (about 2 billion max).
- **Defaults live in the database** (`server_default`), not in Python, so any
  row inserted from anywhere gets the same values.
- **Roast range 0 to 100 is enforced twice**: by a rule inside the database,
  and by a check in the code that rejects a bad number before it gets there.
- **Timestamps keep their timezone**, so nothing breaks if the server is in a
  different country than me.

**Protected topics**

The column is JSONB (a Postgres type that stores JSON), holding a list of
short words. I chose it over a plain list column because it is more flexible
if a topic ever needs more than a name. The trade-off is that the database
accepts any JSON, so keeping it a clean list of text is the code's job.

New members start with the default topics from `helpers/constants.py`. The
plan lists topics only as an example, so making them the default was my call.
It means a new member is protected from them until they remove them. Keeping
the list in one constant also makes it easy to change later.

I first thought about an Enum (a fixed set of allowed values) for the topics.
I dropped it because members can add their own topics, so the list can't be
fixed.

Three functions change the list. `add_protected_topic` and
`remove_protected_topic` work on one topic of a member's own list.
`set_protected_topics` replaces the whole list and is meant for admins. An
empty list clears it.

**Migrations (Alembic)**

Alembic is like git for the database tables. Each change to the tables is a
file, applied with one command, so existing data isn't lost and the history
is recorded. It created `users` in Neon from the `User` class.

It was set up with the async template (`alembic init -t async alembic`)
inside `src`, because Alembic talks to the database in the old blocking way
by default and the app is async. Three edits in `alembic/env.py`:

- The database URL comes from `.env` through the same settings as the rest of
  the app. `alembic.ini` has only a placeholder URL, so no password can end
  up in git.
- `target_metadata = BaseScheme.metadata` tells Alembic what the tables
  should look like.
- `env.py` imports `User`. Importing it is what registers the table with
  `BaseScheme`. Without that import, Alembic sees no tables and generates an
  empty migration.

The first migration (`6d9edffad8e2_create_users_table`) was generated with
`--autogenerate`. Autogenerate compares the code to the database and can miss
things, so I read the file against the `User` class before running it.
Running it also created an `alembic_version` table in Neon, which stores the
last migration that was applied.

When the tables change from now on:

1. Edit or add the class.
2. Add its import to `env.py`.
3. `alembic revision --autogenerate -m "what changed"`, then read the file.
4. `alembic upgrade head`.
5. Apply the same migration to the `test` branch (see Tests).

Migration files go into git, because they are the history of the database.
An applied migration is never edited. A mistake gets a new migration.

**Where the code lives**

I'm copying the folder layout of a reference project: table definitions in
`models/db_schemes/`, operations in `models/*Model.py`, and enums in
`models/enums/` (not created yet, nothing needs one).

- `User.py` says what the data looks like. `UserModel.py` says what the app
  can do with it. A controller calls `UserModel` and never writes queries
  itself.
- `BaseDataModel` is the parent of every `*Model` class and, for now, only
  holds the Session. The Session is opened by whoever receives the work and
  handed to the model, so several models can share one in the same request.
- `BaseScheme` is the parent of every table class. It collects all the
  tables in one place, which is what Alembic reads.

**Registering members**

`get_or_create(discord_id, display_name)` is one database statement. In SQL
it is:

```sql
INSERT INTO users (discord_id, display_name) VALUES (123, 'Ahmed')
ON CONFLICT (discord_id)
DO UPDATE SET display_name = 'Ahmed', last_seen = now()
RETURNING *;
```

A new member is inserted and gets all the defaults. If the `discord_id`
already exists, which would normally be an error because the column is
unique, the statement updates the existing row instead. Only `display_name`
(members rename themselves in Discord) and `last_seen` change. `first_seen`
and the member's settings are not in that update, so they are never touched.

The obvious version is "look the member up, create if missing, update if
found". It has a gap: if two messages from a brand-new member were handled at
the same moment, both would find nothing, both would insert, and one would
fail on the unique rule. The single statement lets the database settle that.
Since I decided every message is handled on its own, this should rarely
happen, but the single statement costs nothing extra.

**Member settings**

Each setting has its own function in `UserModel`, and all of them look the
same: update the row of one `discord_id` and return it.

- `set_roast_intensity` rejects anything outside 0 to 100 with a
  `ValueError`, before the database is involved. 0 means the member is hidden
  from `/roast`, which belongs to Phase 7.
- `set_memory_enabled` lets the member turn memory on or off. Old memories
  are not deleted.
- The protected topic functions normalize the text before storing it: extra
  spaces are trimmed and topics are compared ignoring upper and lower case.
  The topic is stored the way the member wrote it.

These functions don't know who asked. They only receive the `discord_id` of
the member being changed, and the caller decides which ID to pass: the
member's own (Discord attaches it to the command, so the member can't choose
it), or the one an admin picked after checking `is_admin`.

**Admin check**

`is_admin(interaction)` in `helpers/permissions.py` takes the interaction
and returns true or false. Anyone with Discord's Administrator permission is
an admin of the bot. I considered a specific role or a fixed list of IDs, but
for a server of about 10 people that is more setup for no gain.

Discord sends the member's permissions as one number, where each permission
has a fixed value and Administrator is 8. The function checks whether 8 is
part of that number. In a DM there is no server, so there are no permissions
and the answer is always false. A malformed value also gives false. The
request is trusted because its signature was already verified in Phase 1.

The check has to live in the code. Marking a command "admin only" when
registering it with Discord only hides it from the list, and the server owner
can change that in Discord's settings.

**Tests**

The `UserModel` tests run against a separate Neon branch called `test`, whose
URL is `TEST_DATABASE_URL` in `.env`. The test setup refuses to run if that
URL points at the main database, and it empties the `users` table before
every test. There are 20 of them for `UserModel`, and 5 unit tests for
`is_admin` that need no database. All pass.

**Problems along the way**

- **`No module named 'psycopg2'`** (twice, once in `check_db`, once in the
  tests). The URL began with `postgresql://`, so SQLAlchemy picked its
  default blocking driver. Fixed by `postgresql+asyncpg://`.
- **`unexpected keyword argument 'sslmode'`.** asyncpg doesn't know
  `sslmode`. Fixed by keeping only `?ssl=require`.
- **A stale name after an update.** One test registered a member as `Ahmed`,
  registered the same ID again as `Ahmed Ali`, and got `Ahmed` back. The
  database had updated the row correctly. The Session keeps a copy of every
  object it has loaded, and when the same row came back it returned its old
  copy instead of the new data. The fix is `populate_existing=True` on the
  statement, which tells the Session to refresh the copy it holds. It is on
  every statement that returns a row.

**Not verified**

- `get_or_create` isn't called by anything yet. It gets connected in
  Phase 3, and it's undecided whether slash commands should register a member
  too.
- `is_admin` is not attached to any command yet. I assumed Discord includes
  Administrator in the permissions of the server owner. That is from
  Discord's documentation, not something I have tried, so I'll check it on
  the real server. If it's wrong, giving myself a role with Administrator
  fixes it without a code change.
- Nothing uses `get_session()` yet. The tests open their own Session on the
  `test` branch.
