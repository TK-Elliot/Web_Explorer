import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import builtwith
import ssl

class Spider:
    
    def __init__(self) -> None:
        self.url = self.ask_url()
        self.check_url(self.url)
        self.link_list = []
        self.email_address = []
    
    # Ask a user to type URL
    def ask_url(self):
        url = input("\nType your target URL (e.g. https://google.com/): ")
        if not url.endswith("/"):
            url = url + "/"
        return url
    
    # Check if typed URL is valid and reachable   
    def check_url(self, url):
        try:
            return requests.get(url)
        except:
            raise SystemExit("[-] The URL is not reacheable or invalid.")
    
    # Check if a user types URL with a extension
    def invoke_bruteforce(self):
        extensions = input("Type extensions you want to check (e.g. .php,.js,.txt): ")
        self.print_partition("Found subdirectories")
        # When a user type nothing
        # This if statement is necessary because of next elif statement
        if extensions == "":
            self.bruteforce_directory(extensions)
        # When a user forgets to put dot(.)
        elif not "." in extensions:
            print("[-] You need dot(.) before extension.")
        elif " " in extensions:
            print("[-] No space please.")
        else:
            self.bruteforce_directory(extensions)    
    
    # Bruteforce subdirectories with extensions
    def bruteforce_directory(self, extensions):
        extension_list = extensions.split(",")
        with open("directory.txt", "r") as file:
            directory_list = file.readlines()
        for directory in directory_list:
            directory = directory.strip()
            # First time, send directory without extensions
            try: 
                r = requests.get(self.url + directory)
                self.check_directory_found(r, directory)
                for extension in extension_list:
                    if not directory.endswith(extension):
                        directory_with_extension = directory + extension
                        # Delete duplicates
                        # Each word (directory) inside directory_list has newline
                        if not directory_with_extension + "\n" in directory_list:
                            # Send directory with extensions
                            try: 
                                r = requests.get(self.url + directory_with_extension)
                                self.check_directory_found(r, directory_with_extension)
                            except requests.exceptions.ConnectionError:
                                pass
            except requests.exceptions.ConnectionError:
                pass
    
    # Just print out if the directory is found
    def check_directory_found(self, request, directory):
        # If status code is 200, it's in color
        if not request.status_code == 404 and request.status_code == 200:
            print("Directory found: " + directory + " - " + 
                    "Status code: " + "\x1b[6;30;42m" + str(request.status_code) + "\x1b[0m")
        elif not request.status_code == 404:
            print(f"Directory found: {directory} - Status code: {request.status_code}")
    
    # Crawler        
    def extract_link(self, base_url=None, url=None):
        if url == None:
            url = self.url
        if base_url == None:
            base_url = self.url
        try: 
            request = requests.get(url)
            self.find_email_address(request)
            soup = BeautifulSoup(request.text, "html.parser")
            for a_tag in soup.find_all("a"):
                link = a_tag.get("href")
                # Get rid of links when href has nothing or #something
                if not link == None and not "#" in link: 
                    link = urljoin(base_url, link)
                    link = link.split("?")[0]
                    # Get rid of duplicated links and links when link (url) is not target domain
                    if self.url in link and not link in self.link_list:
                        try:
                            r = requests.get(link)
                            # Check if the link is reachable
                            if r.status_code == 200:
                                # Could print links later using self.link_list
                                print(link)
                                self.link_list.append(link)
                                # Recursive
                                self.extract_link(link, link)  
                        except requests.exceptions.ConnectionError:
                            pass 
        except requests.exceptions.ConnectionError:
            pass        
    
    # Print partition
    def print_partition(self, string):
        print(f"\n-------------------{string}-------------------\n")
    
    # Find possible email addresses while crawling
    def find_email_address(self, request):
        email_list = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', request.text)
        for email in email_list:
            # Delete dupicates
            if not email in self.email_address:
                self.email_address.append(email)
        
    # Print email addresses
    def print_email(self):
        self.print_partition("Possible email addresses")
        for email in self.email_address:
            print(email)
    
    # Bruteforce subdomains       
    def bruteforce_subdomain(self):
        self.print_partition("Found subdomains")
        if self.url.startswith("https://www") or self.url.startswith("http://www"):            
            base_url = self.url.replace("www.", "", 1)
        with open("subdomain.txt", "r") as file:
            subdomain_list = file.readlines()
        for subdomain in subdomain_list:
            subdomain = subdomain.strip()
            url = self.concatenate_subdomain(base_url, subdomain)
            try:
                r = requests.get(url)
                print(url)
            except requests.exceptions.ConnectionError:
                pass
    
    # Concatenate subdomain and url        
    def concatenate_subdomain(self, url, subdomain):
        separated_url = url.split("://")
        return separated_url[0] + "://" + subdomain + "." + separated_url[1]
    
    # Detect technology used in the website
    def detect_technology(self):
        # Add this because of an error on Mac
        ssl._create_default_https_context = ssl._create_unverified_context
        result = builtwith.builtwith(self.url)
        self.print_partition("Detected technology")
        for key, value in result.items():
            string_value = ", ".join(value)
            print(key, '->', string_value)
