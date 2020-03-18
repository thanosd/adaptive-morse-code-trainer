from time import sleep

import pyaudio
import math
import random

BITRATE = 8000

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
                       '0': '-----', ', ': '--..--', '.': '.-.-.-',
                       '?': '..--..', '/': '-..-.', '-': '-....-',
                       '(': '-.--.', ')': '-.--.-'}

    koch_order = "KMURESNAPTLWI.JZ=FOY,VG5/Q92H38B?47C1D60X"

    def get_tone(self, duration, quiet=False):
        print(f"duration={duration}")
        samples = int(BITRATE * duration)
        print(f"samples={samples}")
        buffer = ""

        for x in range(samples):
            if not quiet:
                buffer += chr(int(math.sin(x / ((BITRATE / self.frequency) / math.pi)) * 127 + 128))
            else:
                buffer += chr(128)
        print(f"buffer-len={len(buffer)}")
        return buffer

    def __init__(self, frequency=600, char_wpm = 30, farnsworth_wpm = 8):
        self.char_wpm = char_wpm
        self.farnsworth_wpm = farnsworth_wpm
        self.frequency = frequency

        self.dit_time = 60.0 / (50.0 * char_wpm)
        self.dah_time = self.dit_time * 3
        self.farnsworth_time = ((60.0/farnsworth_wpm) - 31*self.dit_time) / 19.0
        print(self.farnsworth_time)

        self.dit = self.get_dit()
        self.dah = self.get_dah()

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.p.get_format_from_width(1),
                        channels=1,
                        rate=BITRATE,
                        output=True)
        self.stream.write(self.get_tone(1, quiet=True))

    def stop(self):
        self.stream.write(self.get_tone(1, quiet=True))
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def get_dit(self):
        return self.get_tone(self.dit_time)

    def get_dah(self):
        return self.get_tone(self.dah_time)

    def get_element_space(self):
        return self.get_tone(self.dit_time, quiet=True)

    def get_char_space(self):
        return self.get_tone(self.farnsworth_time*3, quiet=True)

    def get_word_space(self):
        return self.get_tone(self.farnsworth_time*7, quiet=True)

    def get_audio_for_char(self, c):
        element_space = self.get_element_space()

        upper_c = c.upper()
        elements = []
        if upper_c in MorseGenerator.morse:
            code = MorseGenerator.morse[upper_c]
            for element in code:
                print(element)
                if element == ".":
                    elements.append(self.get_dit())
                elif element == "-":
                    elements.append(self.get_dah())
                else:
                    raise Exception("Gotta be a dit or dash")
            for element in elements:
                print(len(element))
        char_buffer = element_space.join(elements)
        return char_buffer

    def get_audio_for_text(self, s):
        words = []
        in_words = s.split(" ")
        for word in in_words:
            word_buffer = self.get_audio_for_word(word)
            print("foo")
            print(f"len of {word} is {len(word_buffer)}")
            words.append(word_buffer)
        return self.get_word_space().join(words)

    def get_audio_for_word(self, word):

        char_space = self.get_char_space()

        letters = []
        for c in word:
            print(c)


        print(len(char_space))
        word_buffer = char_space.join(letters)
        print(len(word_buffer))
        return word_buffer

    def play(self, s):
        buffer = self.get_audio_for_char(s)
        print(f"writing buffer len = {len(buffer)}")
        half = int(len(buffer) / 2)
        self.stream.write(buffer[0:half])
        self.stream.write(buffer[half:])

def main():

    generator = MorseGenerator()



    starting_koch_index = 5
    random_char = MorseGenerator.koch_order[random.randint(0, starting_koch_index)]


    #generator.play("Hello")
    #generator.play("World")
    print(random_char)
    generator.play(".")
    sleep(1)
    generator.stop()

    #for buffer in generator.get_audio_for_text('Hello world'):
    #    stream.write(buffer)



main()