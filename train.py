import sys
import time
import readchar
import math
import random
import simpleaudio as sa
import curses
import json

BITRATE = 44100

class MorseGenerator:
    morse = {'A': '.-', 'B': '-...',
                       'C': '-.-.', 'D': '-..', 'E': '.',
                       'F': '..-.', 'G': '--.', 'H': '....',
                       'I': '..', 'J': '.---', 'K': '-.-',
                       'L': '.-..', 'M': '--', 'N': '-.',
                       'O': '---', 'P': '.--.', 'Q': '--.-',
                       'R': '.-.', 'S': '...', 'T': '-',
                       'U': '..-', 'V': '...-', 'W': '.--',
                       'X': '-..-', 'Y': '-.--', 'Z': '--..',
                       '1': '.----', '2': '..---', '3': '...--',
                       '4': '....-', '5': '.....', '6': '-....',
                       '7': '--...', '8': '---..', '9': '----.',
                       '0': '-----', ',': '--..--', '.': '.-.-.-',
                       '?': '..--..', '/': '-..-.', '=': '-...-'
                       }

    koch_order = "KMURESNAPTLWI.JZ=FOY,VG5/Q92H38B?47C1D60X"

    def get_tone(self, duration, frequency=None, quiet=False):
        samples = int(BITRATE * duration)
        buffer = bytearray()

        if frequency:
            f = frequency
        else:
            f = self.frequency

        for x in range(samples):
            if not quiet:
                num = int(math.sin(x / ((BITRATE / f) / math.pi)) * 25000 + 32768)
            else:
                num = 32768
            buffer.append(num % 256)
            buffer.append(int(num / 256))
        return buffer

    def __init__(self, frequency=800, char_wpm = 30, farnsworth_wpm = 10):
        self.char_wpm = char_wpm
        self.farnsworth_wpm = farnsworth_wpm
        self.frequency = frequency

        self.dit_time = 60.0 / (50.0 * char_wpm)
        self.dah_time = self.dit_time * 3
        self.farnsworth_time = ((60.0/farnsworth_wpm) - 31*self.dit_time) / 19.0

        self.dit = self.get_dit()
        self.dah = self.get_dah()

    def get_dit(self):
        return self.get_tone(self.dit_time)

    def get_dah(self):
        return self.get_tone(self.dah_time)

    def get_element_space(self):
        return self.get_tone(self.dit_time, quiet=True)

    def get_char_space(self):
        return self.get_tone(self.char_space_duration(), quiet=True)

    def char_space_duration(self):
        return self.farnsworth_time*3

    def get_word_space(self):
        return self.get_tone(self.word_space_duration(), quiet=True)

    def word_space_duration(self):
        return self.farnsworth_time*7

    def get_audio_for_char(self, c):
        element_space = self.get_element_space()

        upper_c = c.upper()
        elements = []
        if upper_c in MorseGenerator.morse:
            code = MorseGenerator.morse[upper_c]
            for element in code:
                if element == ".":
                    elements.append(self.get_dit())
                elif element == "-":
                    elements.append(self.get_dah())
                else:
                    raise Exception("Gotta be a dit or dash")
        char_buffer = element_space.join(elements)
        return char_buffer

    def get_audio_for_text(self, s):
        words = []
        in_words = s.split(" ")
        for word in in_words:
            word_buffer = self.get_audio_for_word(word)
            words.append(word_buffer)
        return self.get_word_space().join(words)

    def get_audio_for_word(self, word):

        char_space = self.get_char_space()
        letters = []
        for c in word:
            letter_buffer = self.get_audio_for_char(c)
            letters.append(letter_buffer)

        word_buffer = char_space.join(letters)
        return word_buffer

    def play(self, s):
        buffer = self.get_audio_for_word(s)
        play_obj = sa.play_buffer(buffer, 1, 2, BITRATE)
        play_obj.wait_done()

    def error_buzz(self):
        buffer = self.get_tone(0.2, 200)
        play_obj = sa.play_buffer(buffer, 1, 2, BITRATE)
        play_obj.wait_done()
        buffer = self.get_tone(0.3, 200, quiet=True)
        play_obj = sa.play_buffer(buffer, 1, 2, BITRATE)
        play_obj.wait_done()

def current_time():
    return int(round(time.time() * 1000))

def read_config():
    try:
        f = open('config.json')
    except FileNotFoundError:
        f = open('config.json', 'w+')

    try:
        config = json.load(f)
    except json.JSONDecodeError as e:
        config = {}

    if "starting_koch_index" not in config:
        config["starting_koch_index"] = 5

    if "rolling_reactions_by_char" not in config:
        config["rolling_reactions_by_char"] = {}
        config["rolling_reactions_by_char"]['*'] = []
        for k in MorseGenerator.morse.keys():
            config["rolling_reactions_by_char"][k] = []

    if "rolling_mistakes_by_char" not in config:
        config["rolling_mistakes_by_char"] = {}
        for k in MorseGenerator.morse.keys():
            config["rolling_mistakes_by_char"][k] = []

    return config

def write_config(c):
    f = open('config.json', 'w')
    json.dump(c, f)


class Display:
    def __init__(self):
        self.screen = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.noecho()

        self.typed_chars = ""

    def update_target_time(self, target_recognition_time):
        self.screen.addstr(0, 0, f"Your target recognition time is {target_recognition_time}ms")

    def update_last_char_time(self, last_char_time, target_recognition_time):
        self.screen.addstr(1, 20, f"Last char: {last_char_time}            ")


        if last_char_time < target_recognition_time:
            total_boxes = int(last_char_time / 20)
            self.screen.addstr(1, 40, "x"*total_boxes + 80*" " )
        else:
            white_boxes = int(target_recognition_time / 20)
            red_boxes = int((last_char_time - target_recognition_time) / 20)
            self.screen.addstr(1, 40, "x" * white_boxes)
            self.screen.addstr(1, 40 + white_boxes, "x" * red_boxes + 80*" ", curses.color_pair(1))

    def update_typed_chars(self, last_char):
        self.typed_chars += last_char
        typed_chars = self.typed_chars[-10:]
        self.screen.addstr(1, 0, f"{typed_chars}                ")

    def display_reaction_times(self, config, target_recognition_time):

        reactions = list()

        for k, v in config["rolling_reactions_by_char"].items():
            if k == '*':
                m = []
            else:
                m = config["rolling_mistakes_by_char"][k]
            reactions.append(ReactionTime(k, v, m))

        reactions.sort(key = lambda r: r.avg, reverse=True)

        index = 2
        for reaction in reactions:
            color = 0
            if reaction.avg > target_recognition_time:
                color = 1
            self.screen.addstr(index, 0, f"{reaction.char}: {reaction.avg:>5} - {reaction.count:>3}       ", curses.color_pair(color))
            index += 1

        reactions.sort(key = lambda r: r.error_ratio, reverse=True)

        index = 2
        for reaction in reactions:
            color = 0
            if reaction.error_ratio > 0.05:
                color = 1
            errors = ["*" if a else " " for a in reaction.moving_mistakes]
            errors_string = "".join(errors)
            self.screen.addstr(index, 40,
                               f"{reaction.char}: - {reaction.error_ratio:.2f}  {errors_string}     ",
                               curses.color_pair(color))
            index += 1

    def get_key(self):
        return self.screen.getkey().upper()

    def show_training_chars(self, chars):
        self.screen.addstr(0, 40, f"Training on: {chars}           ")

    def show_selection_set(self, chars):
        self.screen.addstr(45, 0, f"Selection: {chars}                                  ")

def get_next_random_char(config, training_chars, target_time):
    # We want to weigh numbers with high errors first, and then high delay to come more frequently

    selection_set = ""

    counts = []
    for ch in training_chars:
        react_data = config["rolling_reactions_by_char"][ch]
        mistake_data = config["rolling_mistakes_by_char"][ch]
        r = ReactionTime(ch, react_data, mistake_data)
        counts.append(r.count)
    counts.sort()
    if len(counts) > 0:
        median = counts[int(len(counts) / 2)]
    else:
        median = 0

    accuracy_problematic = ""
    time_problematic = ""
    for ch in training_chars:
        r = ReactionTime(ch, config["rolling_reactions_by_char"][ch], config["rolling_mistakes_by_char"][ch])
        if r.avg > target_time:
            time_problematic += ch
        if r.count < median:
            accuracy_problematic += ch
        elif r.error_ratio > 0.05:
            accuracy_problematic += ch

    selection_set = training_chars

    if len(accuracy_problematic) > 0:
        problematic = accuracy_problematic
    else:
        problematic = time_problematic

    if len(problematic) > 3:
        limit_selection = len(training_chars)
    else:
        limit_selection = max(int(len(training_chars) / 2), 1)

    if len(problematic) > 0:
        extras = ""
        while len(extras) < limit_selection:
            extras += problematic
        selection_set += extras

    selection_set = ''.join(sorted(selection_set))

    return random.choice(selection_set), selection_set



class ReactionTime:

    def __init__(self, chr, moving, moving_mistakes):
        self.char = chr
        self.avg = int(sum(moving) / len(moving)) if len(moving) > 0 else 0
        self.count = len(moving)
        self.moving_mistakes = moving_mistakes

        mistakes = sum(moving_mistakes)
        total_entries = len(moving_mistakes)
        if total_entries == 0:
            self.error_ratio = 0
        else:
            self.error_ratio = 1.0 * mistakes / total_entries


def main():

    config = read_config()

    generator = MorseGenerator()
    display = Display()
    target_recognition_time = int(generator.char_space_duration() * 0.85 * 1000)
    display.update_target_time(target_recognition_time)
    display.display_reaction_times(config, target_recognition_time)

    while True:
        training_chars = MorseGenerator.koch_order[0:config["starting_koch_index"]]
        display.show_training_chars(training_chars)

        random_char, selection_set =  get_next_random_char(config, training_chars, target_recognition_time)
        display.show_selection_set(selection_set)

        not_entered_correctly = True
        while not_entered_correctly:
            generator.play(random_char)
            start_time = current_time()
            try:
                user_input = display.get_key()
            except KeyboardInterrupt:
                # Force an exit
                user_input = "\n"
            if user_input == "\n":
                write_config(config)
                sys.exit(0)
            difference = current_time() - start_time

            # Don't add any really crazy numbers
            if difference > target_recognition_time * 5 or user_input == " ":
                continue

            if random_char != user_input:
                generator.error_buzz()
                config["rolling_mistakes_by_char"][random_char].append(1)
            else:
                config["rolling_mistakes_by_char"][random_char].append(0)

                config["rolling_reactions_by_char"]['*'].append(difference)
                config["rolling_reactions_by_char"][user_input].append(difference)

                config["rolling_reactions_by_char"]['*'] = config["rolling_reactions_by_char"]['*'][-50:]
                config["rolling_reactions_by_char"][user_input] = config["rolling_reactions_by_char"][user_input][-50:]

                display.update_last_char_time(difference, target_recognition_time)
                display.update_typed_chars(user_input)
                not_entered_correctly = False

                config["rolling_mistakes_by_char"][random_char] = config["rolling_mistakes_by_char"][random_char][-50:]

            display.display_reaction_times(config, target_recognition_time)

            add_new_char = True
            for char in training_chars + "*":
                if char == '*':
                    m = []
                else:
                    m = config["rolling_mistakes_by_char"][char]
                r = ReactionTime(char, config["rolling_reactions_by_char"][char], m)
                if r.avg > target_recognition_time or r.count < 25 or r.error_ratio > 0.05:
                    add_new_char = False
                    break
            if add_new_char:
                config["starting_koch_index"] += 1


main()