import datetime
import os
import random
import re
import traceback

import inflect
import requests
from colorama import Back, Fore, Style, init
from requests.exceptions import SSLError


class Word:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

    def __init__(self, word, next_review_date):
        self.word = word
        self.next_review_date = next_review_date
        self.definition = None
        self.origin = None

        if self.next_review_date is None:
            self.next_review_date = datetime.date.today()
        self.get_gpt_definition()

    def update_review_date(self):
        with open('words_to_review.txt', 'r+') as f:
            lines = f.readlines()
            f.seek(0)
            for line in lines:
                f.write(f"{self.word},{self.next_review_date}\n") if line.startswith(
                    self.word) else f.write(line)
            f.truncate()

    def get_gpt_definition(self):  # Use the OpenAI API to get the definition
        retry = True
        while retry:
            try:
                response = requests.post(
                    "https://api.openai.com/v1/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.OPENAI_API_KEY}"
                    },
                    json={
                        "prompt": f"Imagine you are dictionary for B1 english learners. Give an example sentence for '{self.word}' and provide some common synonyms.",
                        "model": 'text-davinci-002',
                        "max_tokens": 500,
                        "temperature": 0.35,
                        "n": 1
                    }
                )
                retry = False
            except SSLError as e:
                print(f"An SSL error occurred: {e}")
                retry = input("Retry request? (y/n): ").lower() == 'y'
                return
            except Exception as e:
                print(f"An error occurred: {e}")
                print(traceback.format_exc())
                return

        with open('gpt_response.txt', 'w', encoding='utf-8') as f:
            f.write(response.text)
        response_data = response.json()
        definition = response_data['choices'][0]['text'].strip()
        # Replace the word with asterisks in the definition, case-insensitive
        asterisks = '*' * len(self.word)
        self.definition = re.sub(re.compile(
            re.escape(self.word), re.IGNORECASE), asterisks, definition)

    def make_one_more_request(self):
        response = requests.post(
            "https://api.openai.com/v1/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.OPENAI_API_KEY}"
            },
            json={
                "prompt": f"Tell me about the origin of the word '{self.word}'.",
                "model": 'text-davinci-002',
                "max_tokens": 500,
                "temperature": 0.5,
                "n": 1
            }
        )
        response_data = response.json()
        self.origin = response_data['choices'][0]['text'].strip()
        print(f"\n{Fore.GREEN}Origin of the word '{self.word}':{Style.RESET_ALL}")
        print(self.origin)

# Calculate the next review date for a word


def calculate_next_review_date(word_instance, num_hidden_letters):
    days_to_wait = num_hidden_letters
    word_instance.next_review_date = (datetime.datetime.now(
    ) + datetime.timedelta(days=days_to_wait)).strftime('%Y-%m-%d')

# Calculate the hidden word


def hide_word(word, num_hidden_letters):
    if num_hidden_letters == len(word):
        num_hidden_letters -= 1
        hidden_word = word[0] + '*' * num_hidden_letters
    elif num_hidden_letters > 0:
        num_hidden_letters -= 1
        hidden_word = word[0] + '*' * num_hidden_letters + \
            word[-(len(word)-num_hidden_letters)+1:]
    return hidden_word, num_hidden_letters


def play_game():
    with open('words_to_review.txt', 'r') as f:
        words = [line.strip() for line in f.readlines()]
    random.shuffle(words)

    total_score = 0
    count = 1
    max_words = 30

    for word in words:
        if count > max_words:
            break
        word = word.strip()
        next_review_date = None
        try:
            next_review_date = word.split(',')[1]
            print('(debug) ', next_review_date)
            next_review_date = datetime.datetime.strptime(
                next_review_date, '%Y-%m-%d').date()
            if next_review_date > datetime.date.today():
                continue
        except IndexError:
            pass

        word = word.split(',')[0]
        word_instance = Word(word, next_review_date)
        if word_instance.definition is None:
            continue

        correct_guess = False
        num_hidden_letters = len(word)
        hidden_word = '*' * num_hidden_letters
        print(f'The {p.ordinal(count)} word: ')
        print(word_instance.definition)
        guessed_word = input("Enter the word that matches the definition: ")
        correct_guess = guessed_word.lower() == word.lower()

        while not correct_guess:
            hidden_word, num_hidden_letters = hide_word(
                word, num_hidden_letters)  # recalculate the hidden word
            print(
                f"{Back.RED}{Fore.WHITE}Sorry, the correct word is '{hidden_word}'.{Style.RESET_ALL}")
            print("Let's try again!")
            guessed_word = input(
                "Enter the word that matches the definition: ")
            correct_guess = guessed_word.lower() == word.lower()

        score = num_hidden_letters * 10
        print(
            f"You saved {Fore.YELLOW}{num_hidden_letters}{Style.RESET_ALL} asterisk(s) and earned {Fore.YELLOW}{score}{Style.RESET_ALL} points.")
        total_score += score

        if num_hidden_letters == 0:
            # All asterisks have been removed, so ask for the word's origin
            word_instance.make_one_more_request()

        calculate_next_review_date(word_instance, num_hidden_letters)
        word_instance.update_review_date()
        print(
            f"The next review date for {Back.BLUE}{Fore.WHITE}'{word_instance.word}'{Style.RESET_ALL} is {Fore.CYAN}{word_instance.next_review_date}{Style.RESET_ALL}\n")
        count += 1

    with open('score.txt', 'r') as f:
        try:
            previous_score = int(f.read())
        except ValueError:
            pass
    with open('score.txt', 'w') as f:
        f.write(str(total_score))
    print(
        f"\nYour total score is {Fore.YELLOW}{total_score}{Style.RESET_ALL} points.")
    print(f"Total score from previous games: {previous_score}")


if __name__ == '__main__':
    init()
    p = inflect.engine()
    play_game()
    input("No more words for the game")
