import sys
import re

# Same function from PartA
# The time complexity for this function would be linear, O(n)
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

# Same fuction as PartA
# The time complexity for this funtion would be O(m)
def computeWordFrequencies(tokens):
    # Using a dictionary/hashmap to make key value pairs
    frequency_map = {}
    for token in tokens:
        if token in frequency_map:
            frequency_map[token] += 1
        else:
            frequency_map[token] = 1
    return frequency_map

# The overall time complexity would be linear, O(n1 + n2 + m1 + m2 + k1 + k2), but on large scale, it is just O(n).
# Where k is from the below intersection method to kind common tokens between the two files
def main():
    # Making sure that 2 txt files are provided in the argument
    if len(sys.argv) != 3:
            print("Please provide the file path for python file and two input text file: python PartB.py <file1_path> <file2_path>")
            sys.exit(1)

    # Getting the file path from each txt file
    file_path1 = sys.argv[1]
    file_path2 = sys.argv[2]

    tokens_file1 = tokenize(file_path1) # running tokenizer for file 1
    tokens_file2 = tokenize(file_path2) # runnign tokenizer for file 2

    frequency_count_file1 = computeWordFrequencies(tokens_file1) # getting the frequency map (unique tokens), for tokens in file 1, even though we don't need the count, we can just easily use intersection
    frequency_count_file2 = computeWordFrequencies(tokens_file2) # getting the frequency map, for tokens in file 2

    common_tokens = set(frequency_count_file1.keys()).intersection(frequency_count_file2.keys()) # using the intersection method to create a set of intersecting keys
    print(len(common_tokens)) # returning the count/number of common keys/tokens

if __name__ == "__main__":
    main()