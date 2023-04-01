import requests
import datetime
import random
import re
import os
from colorama import init, Fore, Style, Back


def get_gpt_definition(word):
    # Use the OpenAI API to get the definition
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    response = requests.post(
        "https://api.openai.com/v1/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        },
        json={
            "prompt": f"Imagine you are dictionary for B1 english learners. Give an example sentence for '{word}' and provide some common synonyms.",
            "model": 'text-davinci-002',
            "max_tokens": 500,
            "temperature": 0.35,
            "n": 1
        }
    )
    with open('gpt_response.txt', 'w', encoding='utf-8') as f:
        f.write(response.text)
    response_data = response.json()
    definition = response_data['choices'][0]['text'].strip()
    # Replace the word with asterisks in the definition, case-insensitive
    asterisks = '*' * len(word)
    definition = re.sub(re.compile(re.escape(word), re.IGNORECASE), asterisks, definition)
    return definition


def get_next_review_date(word):
    with open('words_to_review.txt', 'r+') as f:
        for line in f:
            if word in line:
                if ',' in line:
                    next_review_date = datetime.datetime.strptime(line.strip().split(',')[1], '%Y-%m-%d').date()
                    return next_review_date
                else:
                    break
    return None

# Calculate the next review date for a word
def calculate_next_review_date(num_hidden_letters):
    days_to_wait = num_hidden_letters
    return (datetime.datetime.now() + datetime.timedelta(days=days_to_wait)).strftime('%Y-%m-%d')


def update_review_date(word, next_review_date):
    with open('words_to_review.txt', 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line.startswith(word):
                f.write(f"{word},{next_review_date}\n")
            else:
                f.write(line)
        f.truncate()
    return next_review_date


def review_words(words, max_words=30):
    random.shuffle(words)
    count = 0
    total_score = 0
    previous_score = 0
    for word in words:
        if count >= max_words:
            break
        word = word.strip()
        word = word.split(',')[0]
        next_review_date = get_next_review_date(word)
        if next_review_date is None:
            next_review_date = datetime.date.today()
            update_review_date(word, next_review_date)
        elif next_review_date > datetime.date.today():
            continue
        definition = get_gpt_definition(word)
        print(definition)
        guessed_word = input("Enter the word that matches the definition: ")
        correct_guess = guessed_word.lower() == word.lower()
        hidden_word = word[0] + '*' * (len(word) - 1)
        num_hidden_letters = len(word)
        score = 0
        while not correct_guess:
            print(f"{Back.RED}{Fore.WHITE}Sorry, the correct word is '{hidden_word}'.{Style.RESET_ALL}")
            if num_hidden_letters > 0:
                num_hidden_letters -= 1
                hidden_word = word[0] + '*' * num_hidden_letters + word[-(len(word)-num_hidden_letters-1):]
            guessed_word = input("Enter the word that matches the definition: ")
            correct_guess = guessed_word.lower() == word.lower()
            print("Let's try again!")
        print(f"{Fore.GREEN}Correct! Good job!{Style.RESET_ALL}")
        score += (num_hidden_letters * 10)
        total_score += score
        print(f"You saved {Fore.YELLOW}{num_hidden_letters}{Style.RESET_ALL} asterisk(s) and earned {Fore.YELLOW}{score}{Style.RESET_ALL} points.")
        next_review_date = update_review_date(word, calculate_next_review_date(num_hidden_letters))
        print(f"The next review date for {Back.BLUE}{Fore.WHITE}'{word}'{Style.RESET_ALL} is {Fore.CYAN}{next_review_date}{Style.RESET_ALL}\n")
        
    with open('score.txt', 'r') as f:
        try:
            previous_score = int(f.read())
        except ValueError:
            pass
    with open('score.txt', 'w') as f:
        f.write(str(total_score))
    print(f"\nYour total score is {Fore.YELLOW}{total_score}{Style.RESET_ALL} points.")
    print(f"Total score from previous games: {previous_score}")


if __name__ == '__main__':
    # Get the list of words to review
    with open('words_to_review.txt', 'r') as f:
        words = [line.strip() for line in f.readlines()]
    # Initialize colorama
    init()
    review_words(words)
    input("No more words for the game")
