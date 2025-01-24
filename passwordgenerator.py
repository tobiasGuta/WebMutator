#!/usr/bin/env python3
import click
import requests
import re
import random
import string
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Fetch HTML content of a given URL
def get_html_of(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()  # Raise HTTPError for bad responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

    return resp.content.decode()

# Count occurrences of words in a list that meet a minimum length requirement
def count_occurrences_in(word_list, min_length):
    word_count = {}
    for word in word_list:
        if len(word) < min_length:
            continue
        word_count[word] = word_count.get(word, 0) + 1
    return word_count

# Get all words from the page's raw HTML text
def get_all_words_from(url):
    html = get_html_of(url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    raw_text = soup.get_text()
    return re.findall(r'\w+', raw_text)

# Create common password variations
def generate_password_mutations(base_word):
    mutations = set()

    # Capitalization variations
    mutations.add(base_word.capitalize())  # Capitalized first letter
    mutations.add(base_word.lower())  # All lowercase
    mutations.add(base_word.upper())  # All uppercase

    # Append common numbers, symbols, years, and patterns
    for year in range(2000, 2025):
        mutations.add(f"{base_word}{year}")
    mutations.add(f"{base_word}1!")
    mutations.add(f"{base_word}2!")
    mutations.add(f"{base_word}123")
    mutations.add(f"{base_word}01")
    mutations.add(f"Summer{random.choice(range(2010, 2025))}!")
    
    # Common number sequences
    mutations.add(f"{base_word}1234")
    mutations.add(f"{base_word}0000")
    mutations.add(f"{base_word}1111")
    mutations.add(f"{base_word}qwerty")
    mutations.add(f"{base_word}abcdef")

    # Reverse word and combinations
    mutations.add(f"{base_word[::-1]}")  # Reverse the word
    mutations.add(f"{base_word}{base_word[::-1]}")  # Word + Reversed word

    # Letter substitutions
    mutations.add(f"{base_word.replace('o', '0')}")
    mutations.add(f"{base_word.replace('i', '1')}")
    mutations.add(f"{base_word.replace('a', '@')}")
    mutations.add(f"{base_word.replace('s', '$')}")
    mutations.add(f"{base_word.replace('e', '3')}")

    # Random capitalization
    mutations.add("".join(random.choice([char.upper(), char.lower()]) for char in base_word))

    # Common phrases or words
    mutations.add(f"{base_word}password")
    mutations.add(f"{base_word}admin")
    mutations.add(f"{base_word}letmein")
    mutations.add(f"{base_word}welcome")

    # Time-based variations (random number, symbol, year)
    mutations.add(f"{base_word}{random.randint(1000, 9999)}")
    mutations.add(f"{base_word}{random.choice(['!','@','#','$','%'])}")
    mutations.add(f"{base_word}{random.choice(range(10, 100))}")
    mutations.add(f"{base_word}{random.choice(['2023','2024','2025'])}")

    # Append random characters
    mutations.add(f"{base_word}{''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=4))}")

    # Prepend random characters
    mutations.add(f"{''.join(random.choices(string.ascii_letters + string.digits, k=4))}{base_word}")

    return mutations

# Crawl and extract words and URLs up to the given depth
def crawl_site(url, depth, visited, domain):
    if depth == 0 or url in visited:
        return []
    visited.add(url)

    html = get_html_of(url)
    if not html:
        return []

    # Extract words
    soup = BeautifulSoup(html, 'html.parser')
    raw_text = soup.get_text()
    words = re.findall(r'\w+', raw_text)

    # Extract URLs to crawl next
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(url, href)
        # Check if URL is within the same domain
        if domain in urlparse(full_url).netloc:
            links.append(full_url)

    # Crawl deeper
    for link in links:
        words += crawl_site(link, depth - 1, visited, domain)

    return words

# Get the top words from the list of all words
def get_top_words_from(all_words, min_length):
    occurrences = count_occurrences_in(all_words, min_length)
    return sorted(occurrences.items(), key=lambda item: item[1], reverse=True)

@click.command()
@click.option('--url', '-u', prompt='Web URL', help='URL of webpage to extract from.')
@click.option('--length', '-l', default=0, help='Minimum word length (default: 0, no limit).')
@click.option('--output', '-o', default=None, help='Output file to save results (default: print to console).')
@click.option('--depth', '-d', default=0, help='Crawl depth (default: 0, no crawling).')
def main(url, length, output, depth):
    # Parse the domain of the URL
    domain = urlparse(url).netloc
    visited = set()

    # Get all words from the initial page and its crawled pages if depth > 0
    all_words = crawl_site(url, depth, visited, domain)

    # Get top words based on the specified length
    top_words = get_top_words_from(all_words, length)

    # Generate password mutations for the top words
    all_mutations = []
    for word, _ in top_words[:10]:
        all_mutations.extend(generate_password_mutations(word))

    # Output to file or console
    output_lines = []
    output_lines.append(f"Top words and password mutations from {url}:\n")
    for word in top_words[:10]:
        output_lines.append(f"{word[0]}: {word[1]} occurrences")
    
    output_lines.append("\nGenerated password mutations:\n")
    for mutation in all_mutations:
        output_lines.append(mutation)

    # If output file is specified, write to it
    if output:
        with open(output, 'w') as wr:
            wr.write("\n".join(output_lines))
        print(f"Results saved to {output}")
    else:
        # Otherwise, print to the console
        print("\n".join(output_lines))

if __name__ == '__main__':
    main()

