from bottle import route, run, template, static_file, get, post, request
import json
import pymysql
import os

# Connect to the database


#
connection = pymysql.connect(host='us-cdbr-iron-east-04.cleardb.net',
                             user='bf0322fb12a331',
                             password='97028153',
                             db='heroku_19fdd981997ff6d',
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)

# connection = pymysql.connect(host='localhost',
#                              user='root',
#                              password='',
#                              db='adventure-final',
#                              charset='utf8',
#                              cursorclass=pymysql.cursors.DictCursor)


@route("/", method="GET")
def index():
    return template("adventure.html")


@route("/start", method="POST")
def start():
    username = request.POST.get("username")
    password = request.POST.get("password")
    gender = request.POST.get("gender")
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO `adventure-final`.`users` (`idusers`, `user_name`, `password`, `curr_question`, `user_coins`, `user_life`, `gender`, `prev_answer_id`) " \
                  "VALUES (NULL, '{0}','{1}', '1', '100', '100','{2}', '-1');".format(username, password, gender)
            print("hi1")
            cursor.execute(sql)
            print("hi2")
            connection.commit()
            print("hi3")
    except Exception as e:
        print("you failed because of " + repr(e))
    return json.dumps({"question_num": "",
                       "question_text": "",
                       "answers": [],
                       "image": "choice.jpg"
                       })


def get_user_by_name(username):
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE user_name = '{0}'".format(username)
            cursor.execute(sql)
            return cursor.fetchone()
    except Exception as e:
        pass


def get_question_by_ID(question_ID):
    try:
        with connection.cursor() as cursor:
            sql = "SELECT question_text FROM questions WHERE idquestions = '{0}'".format(question_ID)
            cursor.execute(sql)
            return cursor.fetchone()
    except Exception as e:
        pass


def get_options_for_question(question_ID, prev_answer_ID):
    try:
        with connection.cursor() as cursor:
            prev_question_id = get_previous_question_given_current(question_ID)
            # if we are currently on the first question or last, we don't care what the previous answer was so we query this separately
            if prev_question_id == -1 or prev_question_id == 3:
                sql = "SELECT next_answer_id, answer_text FROM qa_link ql INNER JOIN answers " \
                      "ON ql.next_answer_id = answers.idanswers " \
                      "WHERE ql.prev_question_id = '{0}'".format(prev_question_id)
            else:
                sql = "SELECT next_answer_id, answer_text FROM qa_link ql INNER JOIN answers " \
                      "ON ql.next_answer_id = answers.idanswers " \
                      "WHERE ql.prev_question_id = '{0}' and ql.prev_answer_id = '{1}'".format(prev_question_id, prev_answer_ID)
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        pass


def get_question_for_user(user):
    current_question = get_question_by_ID(user["curr_question"])
    list_of_answers = get_options_for_question(user["curr_question"], user["prev_answer_id"])
    return current_question, list_of_answers


def update_user_current_question(new_curr_question, username):
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE users SET curr_question='{0}' WHERE user_name = '{1}'".format(new_curr_question, username)
            cursor.execute(sql)
            connection.commit()
    except Exception as e:
        print("you failed because of " + repr(e))
    return None


def update_user_prev_answer_id(answer_id, username):
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE users SET prev_answer_id='{}' WHERE user_name = '{}'".format(answer_id, username)
            cursor.execute(sql)
            connection.commit()
    except Exception as e:
        print("you failed because of " + repr(e))
    return None


def get_previous_question_given_current(current_question):
    try:
        with connection.cursor() as cursor:
            sql = "SELECT idquestions FROM questions " \
                  "WHERE next_question_id = '{0}'".format(current_question)
            cursor.execute(sql)
            return cursor.fetchone()["idquestions"]
    except Exception as e:
        print("you failed because of " + repr(e))
    return None


def get_next_question(current_question):
    try:
        with connection.cursor() as cursor:
            sql = "SELECT next_question_id FROM questions " \
                  "WHERE idquestions = '{0}'".format(current_question)
            cursor.execute(sql)
            return cursor.fetchone()["next_question_id"]
    except Exception as e:
        print("you failed because of " + repr(e))
    return None


def get_coins_given_answer_id(answer_id):
    try:
        with connection.cursor() as cursor:
            sql = "SELECT answer_coins FROM answers " \
                  "WHERE idanswers = '{0}'".format(answer_id)
            cursor.execute(sql)
            return cursor.fetchone()["answer_coins"]
    except Exception as e:
        print("you failed because of " + repr(e))
    return None


def get_life_given_answer_id(answer_id):
    try:
        with connection.cursor() as cursor:
            sql = "SELECT answer_life FROM answers " \
                  "WHERE idanswers = '{0}'".format(answer_id)
            cursor.execute(sql)
            return cursor.fetchone()["answer_life"]
    except Exception as e:
        print("you failed because of " + repr(e))
    return None


def update_user_coins_and_life_based_on_answer(user, answer_id):
    coins_to_deduct = int(get_coins_given_answer_id(answer_id))
    life_to_deduct = int(get_life_given_answer_id(answer_id))
    new_amt_coins = max(int(user["user_coins"]) - coins_to_deduct, 0)  # coins cannot be less than 0
    new_amt_life = min(int(user["user_life"]) - life_to_deduct, 100)  # life is capped at 100
    # update the user's values for life and coins
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE users SET user_coins='{0}', user_life='{1}' WHERE user_name = '{2}'"\
                .format(new_amt_coins, new_amt_life, user["user_name"])
            cursor.execute(sql)
            connection.commit()
        print(coins_to_deduct, life_to_deduct)
        return
    except Exception as e:
        print("you failed because of " + repr(e))
    return None


@route("/checkUsernameExists", method="POST")
def check_username_exists():
    username_provided = request.POST.get("username")
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users " \
                  "WHERE user_name = '{0}'".format(username_provided)
            cursor.execute(sql)
            result = cursor.fetchone()  # returns None if there was no match!
            if result:
                return json.dumps({"is_match": 1})
            else:
                return json.dumps({"is_match": 0})
    except Exception as e:
        print("you failed because of " + repr(e))
    return None


@route("/checkUserCredentials", method="POST")
def check_user_credentials():
    username_provided = request.POST.get("username")
    password_provided = request.POST.get("password")
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users " \
                  "WHERE user_name = '{0}' AND password = '{1}'".format(username_provided, password_provided)
            cursor.execute(sql)
            result = cursor.fetchone()  # returns None if there was no match!
            if result:
                return json.dumps({"is_match": 1})
            else:
                return json.dumps({"is_match": 0})
    except Exception as e:
        print("you failed because of " + repr(e))
    return None


@route("/story", method="POST")
def story():
    username = request.POST.get("username")  # TODO: use cookies instead of sending username every time
    user_choice = request.POST.get("choice")  # returns an empty string if has not been sent

    user = get_user_by_name(username)

    # get the next question id from user in order to get the next question
    if user_choice and user["curr_question"]:
        update_user_coins_and_life_based_on_answer(get_user_by_name(username), user_choice)
        update_user_current_question(get_next_question(user["curr_question"]), username)
        update_user_prev_answer_id(user_choice, username)

    # need to get this another time to get updated values of current question and previous answer!
    user = get_user_by_name(username)
    # only get next question for user if it exists
    print(user)
    if user["curr_question"]:
        question_text, list_of_answers = get_question_for_user(user)
        return json.dumps({"question_text": question_text["question_text"],
                           "answers": list_of_answers,
                           "image": "choice.jpg",
                           "is_content": 1,
                           "coins": user["user_coins"],
                           "life": user["user_life"]
                           })
    elif user["user_life"] <= 0:
        return json.dumps({"is_content": 1,
                           "coins": user["user_coins"],
                           "life": user["user_life"]
                           })
    else:
        print("yay this failed without crashing")
        return json.dumps({"is_content": 0})


@route('/js/<filename:re:.*\.js$>', method='GET')
def javascripts(filename):
    return static_file(filename, root='js')


@route('/css/<filename:re:.*\.css>', method='GET')
def stylesheets(filename):
    return static_file(filename, root='css')


@route('/images/<filename:re:.*\.(jpg|png|gif|ico)>', method='GET')
def images(filename):
    return static_file(filename, root='images')


def main():
    # if os.environ.get('APP_LOCATION') == 'heroku':
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    # else:
    #run(host='localhost', port=8080, debug=True)


if __name__ == '__main__':
    main()

