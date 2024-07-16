# brokencameraphone

A cool game. Play it at [https://whisperingcameraphone.com](https://whisperingcameraphone.com).

## Local setup for development

If you want to help with the development of bcp, or just self-host your own
copy of it, that should be pretty easy. But let me know if you have any issues.

 0. (Make sure you have Python 3 and sqlite3 installed)
 1. Clone this repository: `git clone https://github.com/zac-garby/brokencameraphone`
 2. Go to the dev subdirectory: `cd <path where you downloaded it>`
 3. Install the library: `python3 -m pip install .`
 4. Set up the database: `sqlite3 instance/bcp.sqlite3 < schema.sql`
 5. Run the Flask server: `python3 -m flask --app brokencameraphone/app.py run --debug --port 5001`
 6. You should now be able to go to [http://localhost:5001](http://localhost:5001)!
