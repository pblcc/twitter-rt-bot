"""
This file contains the main script for a simple Twitter bot created for retweeting all the Tweets that contain
any hashtag inside of hashtags, for example if the list is: {"programming, "cybersecurity"}, this script
will retweet any tweets that are found with those hashtags (always considering the Twitter API-timeouts).

I have created a Twitter bot using this script, it's called
list of key hashtags, for example #programming.

This bot has been created by Pablo Corbalan, check out his Twitter at: @pablocorbcon

Please do not touch the script, all the configuration should be exported to the configuration.json file!!
"""
import json
import datetime
import tweepy

# Some constants for the script
CONFIGURATION_ROUTE = "configuration.json"
LOGS_ROUTE = "logs.txt"


def get_current_time():
    """
    This function is used for getting the current date and then return it format it as: dd/mm/yy and also return the
    time formatted as: hh:mm
    :return:
    """
    current_date = datetime.date.today().strftime("%d/%m/%Y")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    return f"{current_date} at {current_time}"


def log(msg, log_type="info"):
    """
    This function is used for loading a message into the logs of the application. For example if the msg is equal to
    "Fatal error, the bot has stopped" and it's labeled as an error, it will write: E: fatal error, the bot has
    stopped
    :param msg:str
    :param log_type:str
    """
    log_type = log_type.lower().strip()
    types_hash = {
        "info": "I",
        "error": "E",
    }
    # Evaluate the type and modify the msg depending on it.
    message = msg
    try:
        if log_type != "title":
            t = types_hash[log_type]
            message = f"[{t}]: {msg}"
    except KeyError as _:
        err = "Internal key error when trying to log an error inside the script"
        log(err, log_type="error")
        raise KeyError(err)
    except Exception as e:
        log_undefined_error(e)
    # Now that we have used the type of log to determine the message we have to keep in mind about the
    # title type, that is a bit special cus it writes all in caps.
    if log_type == "title":
        message = f"{msg.upper()}"
    # Now we have a message to be in the logs, so we are going to insert it as: TIME[t]: message
    time = get_current_time()
    message = f"\n{time} | {message}"
    # And finally open the logs and insert
    try:
        with open(LOGS_ROUTE, "a") as f:
            f.write(message)
    except FileNotFoundError as _:
        err = "Can't find the logs file, to save the log..."
        log(err, log_type="error")
        raise FileNotFoundError(err)
    except Exception as e:
        log_undefined_error(e)


def log_undefined_error(e: Exception):
    """
    This method function is used for inserting into the logs an undefined exception, so an exception that is not handled
    in the script that is passed by parameters.
    :param e:exception
    """
    msg = f"An exception is not handled: {e}"
    log(msg, log_type="error")


def to_iso_code(language):
    """
    This function uses a language to return the iso code of it, for example if the language is english, this
    function will return "EN-en", this has been created to simplify the process of configuring the script from
    the json file, so that the user doesn't have to write the actual iso code for it's language.
    :param language: str
    :return:
    """
    languages = {
        # Contains all the languages that are supported and their hash key representation, you can add more of them if
        # you consider it necessary.
        # TODO: Add more languages here if it's necessary, see issue 1 in github.
        "arab": "ar",
        "greek": "el",
        "german": "de",
        "english": "en",
        "spanish": "es",
        "french": "fr",
        "italian": "it",
        "korean": "ko",
        "russian": "ru",
        "chines": "zn"
    }
    language_code = ""
    try:
        language_code = languages[language]
    except KeyError as _:
        # We have to report the error with the corresponding language
        LANGS = '\n   -'.join([i for i in languages.keys()])
        err = f"Sorry, but we can't get the language '{language}'..."
        err += f"\nWe currently have support for the following languages:"
        err += LANGS
        err += "If you think that your language should be supported, you can create a pr on GitHub: "
        err += "\n github.com/pblcc/twitter-rt-bot"
        log(f"Can't find the language requested: {language}", log_type="error")
        raise KeyError(err)
    except Exception as e:
        log_undefined_error(e)
    return language_code


def is_valid_result(result_type):
    """
    This function validates if the type of result is a valid result, this is going to be used for scrapping the tweets,
    so it has to be validated, now (8/3/2021) the following types are supported:
        - mixed
        - recent
        - popular
    You can read more about it here: https://docs.tweepy.org/en/latest/api.html#API.search
    :param result_type:
    :return: The result if it's valid, else will raise KeyError
    """
    r = result_type.strip()
    if r in ["mixed", "recent", "popular"]:
        return r
    # The result is not valid
    err = f"Sorry, but the result type should be: 'mixed', 'recent' or 'popular', you requested '{r}'"
    log("Invalid result type from the configuration", log_type="error")
    raise KeyError(err)


# The first thing we do is loading the configuration for the bot
try:
    with open(CONFIGURATION_ROUTE) as f:
        configuration = json.load(f)
except FileNotFoundError as e:
    err = f"We could not find the configuration file ({CONFIGURATION_ROUTE}), remember to run from the root..."
    log(err, log_type="error")
    raise FileNotFoundError(err)
except Exception as e:
    log_undefined_error(e)

# Extract the credentials from the configuration and then try to create the auth
CONSUMER_KEY, CONSUMER_SECRET = "", ""
ACCESS_TOKEN, ACCESS_TOKEN_SECRET = "", ""
try:
    credentials = configuration["credentials"]
    CONSUMER_KEY = credentials["consumer-key"]
    CONSUMER_SECRET = credentials["consumer-secret"]
except KeyError as e:
    err = "Internal key error when using the credentials..."
    log(err, log_type="error")
    raise KeyError(err)
except Exception as e:
    log_undefined_error(e)

# Create an auth object and access the api of twitter
auth, api = None, None
try:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.api(auth)
except Exception as e:
    log_undefined_error(e)

# Now that we have created the api instance for using the Twitter api, we can actually try to scrape the tweets
# following the rules inside the configuration file.
HASHTAG, MAX_TWEETS, LANGUAGE, RESULT_TYPE = "", "", "", ""
try:
    HASHTAG = configuration["hashtag"]
    MAX_TWEETS = configuration["max-tweets"]
    LANGUAGE = to_iso_code(configuration["language"].lower())
    RESULT_TYPE = is_valid_result(configuration["result-type"].lower())
except KeyError as _:
    err = "Can't parse the configuration for querying the tweets..."
    log(err, log_type="error")
    raise KeyError(err)
except Exception as e:
    log_undefined_error(e)

# Now we have parsed the configuration so we should start scrapping the tweets
tweets = list()
try:
    scrapper = tweepy.Cursor(api.search, q=HASHTAG).items(MAX_TWEETS)
    for t in scrapper:
        current_tweet = {
            "id": t.id,
            "created-at": t.created_at,
            "text": t.text
        }
        tweets.append(current_tweet)
except:
    pass

if __name__ == "__main__":
    log("This is a title for the logs", log_type="title")
    log("This is some information that has to be written at the logs")
    log("This is an error", log_type="error")
    log("This Is Weird")