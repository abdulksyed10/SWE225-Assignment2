import sys
import re

# The required methods are below.
# When executing the program, please run the file and provide the input file in the argument

# The time complexity for this function would be linear, O(n)
# We are reading the file with O(n), where n is the number of characters in the file,
# then tokenizing using regular expression and split using split() is also O(n), overall being O(n).
def tokenize(file_path):
    try:
        # Using utf-8 to only consider common characters and avoiding any errors
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
        
        # Using simple regular expression to only consider alphanumeric characters, will replacing anything else with space
        # so something like "didn't" would have two tokens: "didn" and "t"
        alpha_num = re.sub(r'[^A-Za-z0-9]', ' ', text.lower())
        tokens = alpha_num.split() # splitting the words based on space
        return tokens

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return []     

# The time complexity for this funtion would be O(m)
# Note: it would be O(m) not O(n) since we are just looking at the tokens 
# while the tokenize function looked through the entire file
def computeWordFrequencies(tokens):
    # Using a dictionary/hashmap to make key value pairs
    frequency_map = {}
    for token in tokens:
        if token in frequency_map:
            frequency_map[token] += 1
        else:
            frequency_map[token] = 1
    return frequency_map

# The time complexity for this would be O(k log k), where k is even small than m
# The sorting method time complexity in python in general is O(n log n), in this case it would be O(k log k), 
# while printing each pair is O(n), so for this case it would be O(k)
def PrintFrequencies(word_frequencies):
    decreasing_frequencies = sorted(word_frequencies.items(), key=lambda item: item[1], reverse=True) # using Item two (values/count) to sort the dictionary
    print(decreasing_frequencies)

# The tolal time complexity of the program would be O(n + m + k log k) which would be O(n + k log k)
# The reson it is not just O(n) is because the sorting function, and if a provided file had all unique characters/words then it would still take O(k log k) time, where m would be equal to n 
def main():
    # Making sure the txt file is provided in the argument
    if len(sys.argv) != 2:
            print("Please provide the file path for both python file and the input text file: python PartA.py <file_path>")
            sys.exit(1)

    file_path = sys.argv[1]
    tokens = tokenize(file_path) # running the tokanizer
    frequency_count = computeWordFrequencies(tokens) # calculating the freaquecy count
    PrintFrequencies(frequency_count) 

if __name__ == "__main__":
    main()